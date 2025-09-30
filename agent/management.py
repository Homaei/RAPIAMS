#!/usr/bin/env python3
"""
Enhanced Raspberry Pi Monitoring Agent - Management CLI
Provides command-line management and testing utilities
"""

import sys
import asyncio
import click
import json
import time
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_config import AgentConfig
from enhanced_collector import EnhancedMetricsCollector
from enhanced_sender import EnhancedMetricsSender
from monitoring_modules import (
    SystemMonitor, CPUMonitor, MemoryMonitor, DiskMonitor,
    NetworkMonitor, ProcessMonitor, ServiceMonitor,
    TemperatureMonitor, SecurityMonitor, AlertManager
)

console = Console()


@click.group()
@click.version_option(version="2.0.0-enhanced")
def cli():
    """Enhanced Raspberry Pi Monitoring Agent Management CLI"""
    pass


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
def test(config):
    """Test agent configuration and connectivity"""
    console.print("[bold blue]Testing Enhanced Monitoring Agent[/bold blue]")
    console.print()
    
    try:
        # Load configuration
        if config:
            os.environ['CONFIG_FILE'] = config
        
        agent_config = AgentConfig()
        
        # Display configuration
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_summary = agent_config.get_summary()
        for key, value in config_summary.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            config_table.add_row(key, str(value))
        
        console.print(config_table)
        console.print()
        
        # Test connectivity
        console.print("[bold yellow]Testing API connectivity...[/bold yellow]")
        
        async def test_connectivity():
            sender = EnhancedMetricsSender(agent_config)
            await sender.initialize()
            
            connectivity_result = await sender.test_connectivity()
            
            if connectivity_result['connectivity']:
                console.print("[green]✅ API connectivity: OK[/green]")
                console.print(f"Response time: {connectivity_result['response_time']:.3f}s")
            else:
                console.print("[red]❌ API connectivity: FAILED[/red]")
                if 'error' in connectivity_result:
                    console.print(f"Error: {connectivity_result['error']}")
            
            await sender.close()
            return connectivity_result['connectivity']
        
        connectivity_ok = asyncio.run(test_connectivity())
        
        # Test monitoring modules
        console.print()
        console.print("[bold yellow]Testing monitoring modules...[/bold yellow]")
        
        async def test_modules():
            modules = {
                'System': SystemMonitor(),
                'CPU': CPUMonitor(),
                'Memory': MemoryMonitor(),
                'Disk': DiskMonitor(),
                'Network': NetworkMonitor(),
                'Process': ProcessMonitor(),
                'Service': ServiceMonitor(),
                'Temperature': TemperatureMonitor(),
                'Security': SecurityMonitor(),
                'Alert Manager': AlertManager()
            }
            
            results = {}
            for name, module in modules.items():
                try:
                    if hasattr(module, 'initialize'):
                        success = await module.initialize()
                        results[name] = success
                    else:
                        results[name] = True
                except Exception as e:
                    results[name] = False
                    console.print(f"[red]❌ {name}: {str(e)}[/red]")
            
            return results
        
        module_results = asyncio.run(test_modules())
        
        for module_name, success in module_results.items():
            if success:
                console.print(f"[green]✅ {module_name}: OK[/green]")
            else:
                console.print(f"[red]❌ {module_name}: FAILED[/red]")
        
        # Summary
        console.print()
        successful_modules = sum(1 for success in module_results.values() if success)
        total_modules = len(module_results)
        
        if connectivity_ok and successful_modules == total_modules:
            console.print("[bold green]✅ All tests passed! Agent is ready to run.[/bold green]")
            sys.exit(0)
        else:
            console.print(f"[bold yellow]⚠️  Some tests failed. {successful_modules}/{total_modules} modules OK, Connectivity: {'OK' if connectivity_ok else 'FAILED'}[/bold yellow]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]❌ Test failed: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--duration', '-d', default=60, help='Collection duration in seconds')
def collect(config, duration):
    """Test metrics collection"""
    console.print(f"[bold blue]Testing metrics collection for {duration} seconds[/bold blue]")
    console.print()
    
    try:
        # Load configuration
        if config:
            os.environ['CONFIG_FILE'] = config
        
        agent_config = AgentConfig()
        
        async def collect_metrics():
            # Initialize modules
            modules = {
                'system': SystemMonitor(),
                'cpu': CPUMonitor(),
                'memory': MemoryMonitor(),
                'disk': DiskMonitor(),
                'network': NetworkMonitor(),
                'process': ProcessMonitor(),
                'service': ServiceMonitor(),
                'temperature': TemperatureMonitor(),
                'security': SecurityMonitor()
            }
            
            for module in modules.values():
                if hasattr(module, 'initialize'):
                    await module.initialize()
            
            # Initialize collector
            collector = EnhancedMetricsCollector(agent_config, modules)
            
            # Collect metrics with progress bar
            with Progress() as progress:
                task = progress.add_task("[cyan]Collecting metrics...", total=duration)
                
                start_time = time.time()
                metrics_collected = 0
                
                while time.time() - start_time < duration:
                    try:
                        metrics = await collector.collect_all_metrics()
                        
                        if metrics:
                            metrics_collected += 1
                            
                            # Display sample metrics
                            if metrics_collected == 1:
                                console.print("\n[bold green]Sample metrics collected:[/bold green]")
                                
                                sample_metrics = {
                                    'CPU': f"{metrics.get('cpu_percent', 0):.1f}%",
                                    'Memory': f"{metrics.get('memory_percent', 0):.1f}%",
                                    'Disk': f"{metrics.get('disk_percent', 0):.1f}%",
                                    'Temperature': f"{metrics.get('cpu_temperature', 0):.1f}°C" if metrics.get('cpu_temperature') else 'N/A',
                                    'Uptime': f"{metrics.get('uptime_seconds', 0)} seconds",
                                    'Collection Time': f"{metrics.get('collection_time', 0):.3f}s"
                                }
                                
                                metrics_table = Table()
                                metrics_table.add_column("Metric", style="cyan")
                                metrics_table.add_column("Value", style="green")
                                
                                for metric, value in sample_metrics.items():
                                    metrics_table.add_row(metric, str(value))
                                
                                console.print(metrics_table)
                                console.print()
                        
                        elapsed = time.time() - start_time
                        progress.update(task, completed=elapsed)
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        console.print(f"[red]Error collecting metrics: {str(e)}[/red]")
                        await asyncio.sleep(1)
            
            return metrics_collected
        
        total_collected = asyncio.run(collect_metrics())
        
        console.print(f"[bold green]✅ Collected {total_collected} metric samples in {duration} seconds[/bold green]")
        console.print(f"Average collection rate: {total_collected/duration:.2f} samples/second")
    
    except Exception as e:
        console.print(f"[bold red]❌ Collection test failed: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
def status(config):
    """Show agent status and statistics"""
    console.print("[bold blue]Enhanced Monitoring Agent Status[/bold blue]")
    console.print()
    
    try:
        # Load configuration
        if config:
            os.environ['CONFIG_FILE'] = config
        
        agent_config = AgentConfig()
        
        # System information
        import psutil
        import platform
        
        system_info = Table(title="System Information")
        system_info.add_column("Property", style="cyan")
        system_info.add_column("Value", style="green")
        
        system_info.add_row("Hostname", platform.node())
        system_info.add_row("Platform", f"{platform.system()} {platform.release()}")
        system_info.add_row("Architecture", platform.machine())
        system_info.add_row("Python Version", platform.python_version())
        system_info.add_row("CPU Cores", str(psutil.cpu_count()))
        system_info.add_row("Memory", f"{psutil.virtual_memory().total // (1024**3)} GB")
        system_info.add_row("Boot Time", datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'))
        
        console.print(system_info)
        console.print()
        
        # Agent configuration
        config_info = Table(title="Agent Configuration")
        config_info.add_column("Setting", style="cyan")
        config_info.add_column("Value", style="green")
        
        config_info.add_row("Device ID", agent_config.device_id)
        config_info.add_row("API Endpoint", agent_config.api_endpoint)
        config_info.add_row("Collection Interval", f"{agent_config.collection_interval}s")
        config_info.add_row("Log Level", agent_config.log_level)
        config_info.add_row("Agent Version", agent_config.agent_version)
        
        console.print(config_info)
        console.print()
        
        # Service status (if running as systemd service)
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-active', 'rpi-monitoring-agent'],
                capture_output=True, text=True
            )
            
            service_status = "Active" if result.returncode == 0 else "Inactive"
            status_color = "green" if result.returncode == 0 else "red"
            
            console.print(f"Service Status: [{status_color}]{service_status}[/{status_color}]")
            
            if result.returncode == 0:
                # Get service info
                result = subprocess.run(
                    ['systemctl', 'show', 'rpi-monitoring-agent', '--property=ActiveState,SubState,MainPID,ExecMainStartTimestamp'],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            console.print(f"  {key}: {value}")
        
        except Exception:
            console.print("[yellow]Service status: Unknown (not installed as systemd service)[/yellow]")
    
    except Exception as e:
        console.print(f"[bold red]❌ Status check failed: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--api-endpoint', prompt=True, help='API endpoint URL')
@click.option('--api-key', prompt=True, hide_input=True, help='API key')
@click.option('--device-id', default='', help='Device ID (default: hostname)')
@click.option('--output', '-o', default='agent_config.json', help='Output configuration file')
def configure(api_endpoint, api_key, device_id, output):
    """Generate configuration file"""
    import socket
    
    if not device_id:
        device_id = socket.gethostname()
    
    config = {
        "api_endpoint": api_endpoint,
        "api_key": api_key,
        "device_id": device_id,
        "collection_interval": 30,
        "log_level": "INFO",
        "enable_detailed_monitoring": True,
        "enable_process_monitoring": True,
        "enable_service_monitoring": True,
        "enable_security_monitoring": True,
        "enable_network_monitoring": True,
        "enable_gpio_monitoring": True,
        "gpio_pins": [],
        "custom_scripts": {},
        "alert_thresholds": {
            "cpu_percent": {"info": 30.0, "warning": 70.0, "critical": 85.0, "danger": 95.0},
            "memory_percent": {"info": 50.0, "warning": 75.0, "critical": 85.0, "danger": 95.0},
            "disk_percent": {"info": 60.0, "warning": 75.0, "critical": 85.0, "danger": 95.0},
            "temperature_celsius": {"info": 40.0, "warning": 60.0, "critical": 75.0, "danger": 85.0}
        }
    }
    
    try:
        with open(output, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✅ Configuration saved to {output}[/green]")
        console.print()
        console.print("Configuration summary:")
        console.print(f"- API Endpoint: {api_endpoint}")
        console.print(f"- Device ID: {device_id}")
        console.print(f"- Collection Interval: 30 seconds")
        console.print()
        console.print("You can now run the agent with:")
        console.print(f"python3 enhanced_main.py --config {output}")
    
    except Exception as e:
        console.print(f"[red]❌ Failed to save configuration: {str(e)}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()