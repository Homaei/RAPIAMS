"""
User Manager Module
Advanced user management and monitoring capabilities
"""

import pwd
import grp
import os
import time
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
from collections import deque
import psutil


class UserManager:
    def __init__(self, history_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.login_history = deque(maxlen=history_size)
        self.user_activity_history = {}
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()

    def get_all_users(self) -> Dict[str, Any]:
        """Get comprehensive information about all system users"""
        try:
            users = {}
            user_count = {
                'total': 0,
                'system': 0,
                'regular': 0,
                'active': 0,
                'with_shell': 0,
                'with_home': 0
            }

            for user in pwd.getpwall():
                user_info = self._get_user_details(user)
                users[user.pw_name] = user_info

                # Count statistics
                user_count['total'] += 1
                if user_info['is_system_user']:
                    user_count['system'] += 1
                else:
                    user_count['regular'] += 1

                if user_info['has_valid_shell']:
                    user_count['with_shell'] += 1

                if user_info['has_home_directory']:
                    user_count['with_home'] += 1

            # Count currently active users
            active_users = self.get_active_users()
            user_count['active'] = len(active_users.get('users', []))

            return {
                'timestamp': datetime.now().isoformat(),
                'users': users,
                'statistics': user_count
            }

        except Exception as e:
            self.logger.error(f"Error getting all users: {e}")
            return {"error": str(e)}

    def get_active_users(self) -> Dict[str, Any]:
        """Get currently logged in users"""
        try:
            active_users = []
            unique_users = set()

            for user in psutil.users():
                user_info = {
                    'username': user.name,
                    'terminal': user.terminal,
                    'host': user.host if user.host else 'local',
                    'started': datetime.fromtimestamp(user.started).isoformat() if user.started else None,
                    'session_duration': self._calculate_session_duration(user.started) if user.started else None
                }
                active_users.append(user_info)
                unique_users.add(user.name)

            return {
                'timestamp': datetime.now().isoformat(),
                'users': active_users,
                'unique_users': list(unique_users),
                'total_sessions': len(active_users),
                'unique_user_count': len(unique_users)
            }

        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return {"error": str(e)}

    def get_user_details(self, username: str) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        try:
            # Get user from passwd
            try:
                user = pwd.getpwnam(username)
            except KeyError:
                return {"error": f"User '{username}' not found"}

            user_details = self._get_user_details(user)

            # Add additional details
            user_details.update({
                'groups': self._get_user_groups(username),
                'sudo_access': self._check_sudo_access(username),
                'recent_activity': self._get_user_recent_activity(username),
                'process_count': self._get_user_process_count(username),
                'disk_usage': self._get_user_disk_usage(user.pw_dir) if user.pw_dir else None
            })

            return {
                'timestamp': datetime.now().isoformat(),
                'user': user_details
            }

        except Exception as e:
            self.logger.error(f"Error getting user details for {username}: {e}")
            return {"error": str(e)}

    def get_user_groups(self, username: str = None) -> Dict[str, Any]:
        """Get user groups information"""
        try:
            if username:
                # Get groups for specific user
                user_groups = self._get_user_groups(username)
                return {
                    'timestamp': datetime.now().isoformat(),
                    'username': username,
                    'groups': user_groups
                }
            else:
                # Get all groups
                all_groups = {}
                for group in grp.getgrall():
                    all_groups[group.gr_name] = {
                        'gid': group.gr_gid,
                        'members': group.gr_mem
                    }

                return {
                    'timestamp': datetime.now().isoformat(),
                    'groups': all_groups,
                    'total_groups': len(all_groups)
                }

        except Exception as e:
            self.logger.error(f"Error getting user groups: {e}")
            return {"error": str(e)}

    def get_login_history(self, username: str = None, days: int = 7) -> Dict[str, Any]:
        """Get login history from system logs"""
        try:
            login_events = []

            # Try to read from various log sources
            log_sources = [
                '/var/log/auth.log',
                '/var/log/secure',
                '/var/log/wtmp'
            ]

            for log_file in log_sources:
                if os.path.exists(log_file):
                    events = self._parse_login_logs(log_file, username, days)
                    login_events.extend(events)

            # Also try using 'last' command
            last_events = self._get_last_command_output(username, days)
            login_events.extend(last_events)

            # Sort by timestamp
            login_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            # Remove duplicates and limit results
            seen = set()
            unique_events = []
            for event in login_events:
                event_key = f"{event.get('username', '')}_{event.get('timestamp', '')}_{event.get('type', '')}"
                if event_key not in seen:
                    seen.add(event_key)
                    unique_events.append(event)
                    if len(unique_events) >= 100:  # Limit to 100 events
                        break

            return {
                'timestamp': datetime.now().isoformat(),
                'events': unique_events,
                'total_events': len(unique_events),
                'query_days': days,
                'query_user': username
            }

        except Exception as e:
            self.logger.error(f"Error getting login history: {e}")
            return {"error": str(e)}

    def get_user_security_info(self, username: str = None) -> Dict[str, Any]:
        """Get security-related information about users"""
        try:
            if username:
                # Security info for specific user
                try:
                    user = pwd.getpwnam(username)
                except KeyError:
                    return {"error": f"User '{username}' not found"}

                security_info = {
                    'username': username,
                    'uid': user.pw_uid,
                    'is_system_user': user.pw_uid < 1000,
                    'has_password': self._check_user_has_password(username),
                    'password_status': self._get_password_status(username),
                    'sudo_access': self._check_sudo_access(username),
                    'shell': user.pw_shell,
                    'shell_access': user.pw_shell not in ['/bin/false', '/usr/sbin/nologin', '/bin/nologin'],
                    'groups': self._get_user_groups(username),
                    'home_directory': user.pw_dir,
                    'home_exists': os.path.exists(user.pw_dir) if user.pw_dir else False
                }

                return {
                    'timestamp': datetime.now().isoformat(),
                    'user_security': security_info
                }
            else:
                # Security overview for all users
                security_summary = {
                    'total_users': 0,
                    'privileged_users': [],
                    'users_with_shell': [],
                    'users_without_password': [],
                    'system_users': [],
                    'regular_users': []
                }

                for user in pwd.getpwall():
                    security_summary['total_users'] += 1

                    if user.pw_uid < 1000:
                        security_summary['system_users'].append(user.pw_name)
                    else:
                        security_summary['regular_users'].append(user.pw_name)

                    if user.pw_shell not in ['/bin/false', '/usr/sbin/nologin', '/bin/nologin']:
                        security_summary['users_with_shell'].append(user.pw_name)

                    if self._check_sudo_access(user.pw_name):
                        security_summary['privileged_users'].append(user.pw_name)

                    if not self._check_user_has_password(user.pw_name):
                        security_summary['users_without_password'].append(user.pw_name)

                return {
                    'timestamp': datetime.now().isoformat(),
                    'security_summary': security_summary
                }

        except Exception as e:
            self.logger.error(f"Error getting user security info: {e}")
            return {"error": str(e)}

    def create_user(self, username: str, password: str = None, shell: str = '/bin/bash',
                   home_dir: str = None, groups: List[str] = None) -> Dict[str, Any]:
        """Create a new user (requires root privileges)"""
        try:
            if os.geteuid() != 0:
                return {"error": "Root privileges required to create users"}

            # Check if user already exists
            try:
                pwd.getpwnam(username)
                return {"error": f"User '{username}' already exists"}
            except KeyError:
                pass  # User doesn't exist, which is what we want

            # Build useradd command
            cmd = ['useradd']

            if shell:
                cmd.extend(['-s', shell])

            if home_dir:
                cmd.extend(['-d', home_dir])
            else:
                cmd.extend(['-m'])  # Create home directory

            if groups:
                cmd.extend(['-G', ','.join(groups)])

            cmd.append(username)

            # Execute useradd command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return {
                    "error": f"Failed to create user: {result.stderr}",
                    "command": ' '.join(cmd)
                }

            # Set password if provided
            if password:
                passwd_result = self._set_user_password(username, password)
                if 'error' in passwd_result:
                    return passwd_result

            return {
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'message': f"User '{username}' created successfully",
                'user_details': self.get_user_details(username)
            }

        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
            return {"error": str(e)}

    def delete_user(self, username: str, remove_home: bool = False) -> Dict[str, Any]:
        """Delete a user (requires root privileges)"""
        try:
            if os.geteuid() != 0:
                return {"error": "Root privileges required to delete users"}

            # Check if user exists
            try:
                user = pwd.getpwnam(username)
            except KeyError:
                return {"error": f"User '{username}' not found"}

            # Build userdel command
            cmd = ['userdel']
            if remove_home:
                cmd.append('-r')
            cmd.append(username)

            # Execute userdel command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return {
                    "error": f"Failed to delete user: {result.stderr}",
                    "command": ' '.join(cmd)
                }

            return {
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'message': f"User '{username}' deleted successfully",
                'removed_home': remove_home
            }

        except Exception as e:
            self.logger.error(f"Error deleting user {username}: {e}")
            return {"error": str(e)}

    def start_monitoring(self, interval: float = 60.0):
        """Start continuous user activity monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("User monitoring started")

    def stop_monitoring(self):
        """Stop continuous user monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("User monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                timestamp = datetime.now()

                # Monitor active users
                active_users = self.get_active_users()

                with self._lock:
                    self.login_history.append({
                        'timestamp': timestamp,
                        'active_users': active_users.get('unique_users', []),
                        'session_count': active_users.get('total_sessions', 0)
                    })

                time.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in user monitoring loop: {e}")
                time.sleep(interval)

    def _get_user_details(self, user) -> Dict[str, Any]:
        """Get detailed information about a user"""
        return {
            'username': user.pw_name,
            'uid': user.pw_uid,
            'gid': user.pw_gid,
            'full_name': user.pw_gecos,
            'home_directory': user.pw_dir,
            'shell': user.pw_shell,
            'is_system_user': user.pw_uid < 1000,
            'has_valid_shell': user.pw_shell not in ['/bin/false', '/usr/sbin/nologin', '/bin/nologin'],
            'has_home_directory': os.path.exists(user.pw_dir) if user.pw_dir else False,
            'last_login': self._get_last_login(user.pw_name)
        }

    def _get_user_groups(self, username: str) -> List[Dict[str, Any]]:
        """Get groups for a specific user"""
        groups = []
        try:
            # Primary group
            user = pwd.getpwnam(username)
            primary_group = grp.getgrgid(user.pw_gid)
            groups.append({
                'name': primary_group.gr_name,
                'gid': primary_group.gr_gid,
                'is_primary': True
            })

            # Secondary groups
            for group in grp.getgrall():
                if username in group.gr_mem:
                    groups.append({
                        'name': group.gr_name,
                        'gid': group.gr_gid,
                        'is_primary': False
                    })

        except Exception as e:
            self.logger.debug(f"Error getting groups for {username}: {e}")

        return groups

    def _check_sudo_access(self, username: str) -> bool:
        """Check if user has sudo access"""
        try:
            # Check if user is in sudo or wheel group
            sudo_groups = ['sudo', 'wheel', 'admin']
            user_groups = [g['name'] for g in self._get_user_groups(username)]

            for sudo_group in sudo_groups:
                if sudo_group in user_groups:
                    return True

            # Check sudoers file (basic check)
            try:
                result = subprocess.run(['sudo', '-l', '-U', username],
                                      capture_output=True, text=True, timeout=5)
                return 'may run the following commands' in result.stdout
            except:
                pass

        except Exception as e:
            self.logger.debug(f"Error checking sudo access for {username}: {e}")

        return False

    def _get_user_recent_activity(self, username: str) -> Dict[str, Any]:
        """Get recent activity for a user"""
        try:
            # Check if user is currently logged in
            active_users = self.get_active_users()
            is_active = username in active_users.get('unique_users', [])

            # Get user processes
            process_count = self._get_user_process_count(username)

            return {
                'is_currently_active': is_active,
                'process_count': process_count,
                'last_login': self._get_last_login(username)
            }

        except Exception as e:
            self.logger.debug(f"Error getting recent activity for {username}: {e}")
            return {}

    def _get_user_process_count(self, username: str) -> int:
        """Get number of processes owned by user"""
        try:
            count = 0
            for proc in psutil.process_iter(['username']):
                try:
                    if proc.info['username'] == username:
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except:
            return 0

    def _get_user_disk_usage(self, home_dir: str) -> Optional[Dict[str, Any]]:
        """Get disk usage for user's home directory"""
        try:
            if not os.path.exists(home_dir):
                return None

            result = subprocess.run(['du', '-sh', home_dir],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                return {'home_directory_size': size}

        except Exception as e:
            self.logger.debug(f"Error getting disk usage for {home_dir}: {e}")

        return None

    def _check_user_has_password(self, username: str) -> bool:
        """Check if user has a password set"""
        try:
            result = subprocess.run(['passwd', '-S', username],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Output format: username P/NP/L date...
                status = result.stdout.split()[1] if len(result.stdout.split()) > 1 else 'NP'
                return status == 'P'  # P = password set
        except:
            pass
        return False

    def _get_password_status(self, username: str) -> str:
        """Get password status for user"""
        try:
            result = subprocess.run(['passwd', '-S', username],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                parts = result.stdout.split()
                if len(parts) > 1:
                    status = parts[1]
                    status_map = {
                        'P': 'Password set',
                        'NP': 'No password',
                        'L': 'Locked'
                    }
                    return status_map.get(status, 'Unknown')
        except:
            pass
        return 'Unknown'

    def _get_last_login(self, username: str) -> Optional[str]:
        """Get last login time for user"""
        try:
            result = subprocess.run(['last', '-n', '1', username],
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 0 and 'wtmp begins' not in lines[0]:
                    # Parse last output
                    return lines[0].strip()
        except:
            pass
        return None

    def _set_user_password(self, username: str, password: str) -> Dict[str, Any]:
        """Set password for user"""
        try:
            proc = subprocess.Popen(['passwd', username],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True)

            stdout, stderr = proc.communicate(input=f"{password}\n{password}\n")

            if proc.returncode != 0:
                return {"error": f"Failed to set password: {stderr}"}

            return {"success": True, "message": "Password set successfully"}

        except Exception as e:
            return {"error": f"Error setting password: {e}"}

    def _parse_login_logs(self, log_file: str, username: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """Parse login events from log files"""
        events = []
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with open(log_file, 'r') as f:
                for line in f:
                    # Simple parsing - this would need to be more sophisticated for production
                    if 'session opened' in line or 'session closed' in line:
                        if username is None or username in line:
                            events.append({
                                'raw_log': line.strip(),
                                'timestamp': datetime.now().isoformat(),  # Simplified
                                'type': 'login' if 'opened' in line else 'logout',
                                'source': log_file
                            })

        except Exception as e:
            self.logger.debug(f"Error parsing {log_file}: {e}")

        return events

    def _get_last_command_output(self, username: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get login history using 'last' command"""
        events = []
        try:
            cmd = ['last']
            if username:
                cmd.append(username)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and 'wtmp begins' not in line:
                        events.append({
                            'raw_log': line.strip(),
                            'timestamp': datetime.now().isoformat(),  # Simplified
                            'type': 'login_history',
                            'source': 'last_command'
                        })

        except Exception as e:
            self.logger.debug(f"Error running 'last' command: {e}")

        return events

    @staticmethod
    def _calculate_session_duration(start_timestamp: float) -> str:
        """Calculate session duration"""
        try:
            start_time = datetime.fromtimestamp(start_timestamp)
            duration = datetime.now() - start_time

            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        except:
            return "Unknown"


# Example usage
if __name__ == "__main__":
    manager = UserManager()

    print("=== All Users ===")
    all_users = manager.get_all_users()
    print(json.dumps(all_users, indent=2))

    print("\n=== Active Users ===")
    active_users = manager.get_active_users()
    print(json.dumps(active_users, indent=2))

    print("\n=== User Security Info ===")
    security_info = manager.get_user_security_info()
    print(json.dumps(security_info, indent=2))