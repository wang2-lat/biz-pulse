import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import sys

from database import Database

app = typer.Typer(help="Lightweight CLI tool for small business management")
console = Console()
db = Database()

# Customer commands
customer_app = typer.Typer(help="Manage customers")
app.add_typer(customer_app, name="customer")

@customer_app.command("add")
def add_customer(
    name: str = typer.Argument(..., help="Customer name"),
    email: str = typer.Option("", help="Email address"),
    phone: str = typer.Option("", help="Phone number"),
    stage: str = typer.Option("lead", help="Sales stage: lead/contact/proposal/negotiation")
):
    """Add a new customer"""
    customer_id = db.add_customer(name, email, phone, stage)
    console.print(f"[green]✓[/green] Customer added (ID: {customer_id})")

@customer_app.command("list")
def list_customers(
    status: str = typer.Option("all", help="Filter by status: all/active/won/lost")
):
    """List all customers"""
    customers = db.get_customers(status)
    
    table = Table(title="Customers")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email")
    table.add_column("Phone")
    table.add_column("Stage")
    table.add_column("Status")
    
    for c in customers:
        table.add_row(str(c[0]), c[1], c[2], c[3], c[4], c[5])
    
    console.print(table)

@customer_app.command("update")
def update_customer(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    stage: str = typer.Option(None, help="New stage"),
    status: str = typer.Option(None, help="New status: active/won/lost")
):
    """Update customer stage or status"""
    db.update_customer(customer_id, stage, status)
    console.print(f"[green]✓[/green] Customer {customer_id} updated")

# Deal commands
deal_app = typer.Typer(help="Manage deals")
app.add_typer(deal_app, name="deal")

@deal_app.command("add")
def add_deal(
    customer_id: int = typer.Argument(..., help="Customer ID"),
    amount: float = typer.Argument(..., help="Deal amount"),
    stage: str = typer.Option("proposal", help="Deal stage")
):
    """Add a new deal"""
    deal_id = db.add_deal(customer_id, amount, stage)
    console.print(f"[green]✓[/green] Deal added (ID: {deal_id})")

@deal_app.command("list")
def list_deals():
    """List all deals"""
    deals = db.get_deals()
    
    table = Table(title="Deals")
    table.add_column("ID", style="cyan")
    table.add_column("Customer")
    table.add_column("Amount", style="green")
    table.add_column("Stage")
    table.add_column("Status")
    
    for d in deals:
        table.add_row(str(d[0]), d[1], f"${d[2]:.2f}", d[3], d[4])
    
    console.print(table)

@deal_app.command("won")
def mark_deal_won(deal_id: int = typer.Argument(..., help="Deal ID")):
    """Mark deal as won"""
    db.update_deal_status(deal_id, "won")
    console.print(f"[green]✓[/green] Deal {deal_id} marked as won")

@deal_app.command("lost")
def mark_deal_lost(deal_id: int = typer.Argument(..., help="Deal ID")):
    """Mark deal as lost"""
    db.update_deal_status(deal_id, "lost")
    console.print(f"[yellow]✓[/yellow] Deal {deal_id} marked as lost")

# Stats commands
@app.command("stats")
def show_stats():
    """Show business statistics"""
    stats = db.get_stats()
    
    panel = Panel(
        f"[green]Won This Month:[/green] {stats['won_this_month']}\n"
        f"[yellow]Active Deals:[/yellow] {stats['active_deals']}\n"
        f"[red]At Risk Customers:[/red] {stats['at_risk']}\n"
        f"[cyan]Total Revenue:[/cyan] ${stats['total_revenue']:.2f}",
        title="Business Stats",
        border_style="blue"
    )
    console.print(panel)
    
    # Sales funnel
    funnel = db.get_funnel()
    table = Table(title="Sales Funnel")
    table.add_column("Stage", style="cyan")
    table.add_column("Count", style="green")
    
    for stage, count in funnel.items():
        table.add_row(stage, str(count))
    
    console.print(table)

# Meeting commands
meeting_app = typer.Typer(help="Manage meetings")
app.add_typer(meeting_app, name="meeting")

@meeting_app.command("add")
def add_meeting(
    title: str = typer.Argument(..., help="Meeting title"),
    notes: str = typer.Option("", help="Meeting notes")
):
    """Record a meeting"""
    meeting_id = db.add_meeting(title, notes)
    console.print(f"[green]✓[/green] Meeting recorded (ID: {meeting_id})")

@meeting_app.command("list")
def list_meetings():
    """List all meetings"""
    meetings = db.get_meetings()
    
    table = Table(title="Meetings")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Date")
    table.add_column("Notes")
    
    for m in meetings:
        table.add_row(str(m[0]), m[1], m[2], m[3][:50] if m[3] else "")
    
    console.print(table)

# Task commands
task_app = typer.Typer(help="Manage tasks")
app.add_typer(task_app, name="task")

@task_app.command("add")
def add_task(
    description: str = typer.Argument(..., help="Task description"),
    assignee: str = typer.Argument(..., help="Assignee name"),
    meeting_id: int = typer.Option(None, help="Related meeting ID")
):
    """Add a new task"""
    task_id = db.add_task(description, assignee, meeting_id)
    console.print(f"[green]✓[/green] Task added (ID: {task_id})")

@task_app.command("list")
def list_tasks(
    status: str = typer.Option("pending", help="Filter by status: pending/done/all")
):
    """List tasks"""
    tasks = db.get_tasks(status)
    
    table = Table(title="Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Assignee")
    table.add_column("Status")
    table.add_column("Created")
    
    for t in tasks:
        table.add_row(str(t[0]), t[1], t[2], t[3], t[4])
    
    console.print(table)

@task_app.command("done")
def mark_task_done(task_id: int = typer.Argument(..., help="Task ID")):
    """Mark task as done"""
    db.update_task_status(task_id, "done")
    console.print(f"[green]✓[/green] Task {task_id} marked as done")

if __name__ == "__main__":
    app()
