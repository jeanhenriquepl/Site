from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, SQLModel
from typing import List
from datetime import datetime, timedelta

from .database import create_db_and_tables, get_session
from sqlalchemy.orm import selectinload
from .models import Machine, Software, Service, InventoryReport, MachineRead

app = FastAPI(title="IT Inventory System", version="1.0.0")

# CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity in this project
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/api/inventory", response_model=Machine)
def create_inventory(report: InventoryReport, session: Session = Depends(get_session)):
    # Check if machine exists
    statement = select(Machine).where(Machine.hostname == report.hostname)
    existing_machine = session.exec(statement).first()

    if existing_machine:
        machine = existing_machine
        machine.client_code = report.client_code or "DEFAULT"
        machine.ip_address = report.ip_address
        machine.os_info = report.os_info
        machine.processor = report.processor
        machine.ram_gb = report.ram_gb
        machine.disk_gb = report.disk_gb
        machine.manufacturer = report.manufacturer
        machine.model = report.model
        machine.serial_number = report.serial_number
        machine.last_seen = datetime.utcnow()
        
        # Update metrics
        machine.cpu_usage = report.cpu_usage
        machine.memory_usage = report.memory_usage
        machine.disk_usage = report.disk_usage
        
        # Alert Logic
        machine.status = "online"
        machine.alert_message = None
        
        if report.disk_usage and report.disk_usage > 90:
            machine.status = "critical"
            machine.alert_message = "Storage Critical (>90%)"
        elif report.memory_usage and report.memory_usage > 90:
            machine.status = "warning"
            machine.alert_message = "High Memory Usage (>90%)"
            
        # Remove old software to replace with new scan (simple approach)
        for software in machine.softwares:
            session.delete(software)
        # Remove old services
        for service in machine.services:
            session.delete(service)
    else:
        # Initial Alert Logic for new machine
        status = "online"
        alert_msg = None
        if report.disk_usage and report.disk_usage > 90:
            status = "critical"
            alert_msg = "Storage Critical (>90%)"
        elif report.memory_usage and report.memory_usage > 90:
            status = "warning"
            alert_msg = "High Memory Usage (>90%)"
            
        machine = Machine(
            hostname=report.hostname,
            client_code=report.client_code or "DEFAULT",
            ip_address=report.ip_address,
            os_info=report.os_info,
            processor=report.processor,
            ram_gb=report.ram_gb,
            disk_gb=report.disk_gb,
            manufacturer=report.manufacturer,
            model=report.model,
            serial_number=report.serial_number,
            last_seen=datetime.utcnow(),
            cpu_usage=report.cpu_usage,
            memory_usage=report.memory_usage,
            disk_usage=report.disk_usage,
            status=status,
            alert_message=alert_msg
        )
        session.add(machine)
    
    session.commit()
    session.refresh(machine)

    # Add softwares
    if report.softwares:
        for soft_data in report.softwares:
            software = Software(
                name=soft_data.get("name"),
                version=soft_data.get("version"),
                publisher=soft_data.get("publisher"),
                machine_id=machine.id
            )
            session.add(software)
    
    # Add services
    if report.services:
        for svc_data in report.services:
            service = Service(
                name=svc_data.get("name"),
                display_name=svc_data.get("display_name"),
                status=svc_data.get("status"),
                start_type=svc_data.get("start_type"),
                machine_id=machine.id
            )
            session.add(service)
    
    session.commit()
    session.refresh(machine)
    return machine

@app.get("/api/machines", response_model=List[MachineRead])
def read_machines(session: Session = Depends(get_session)):
    # Eager load for CSV export support
    query = select(Machine).options(
        selectinload(Machine.softwares),
        selectinload(Machine.services)
    )
    machines = session.exec(query).all()
    return machines

@app.get("/api/machines/{machine_id}", response_model=MachineRead)
def read_machine(machine_id: int, session: Session = Depends(get_session)):
    # Eager load softwares and services
    query = select(Machine).where(Machine.id == machine_id).options(
        selectinload(Machine.softwares),
        selectinload(Machine.services)
    )
    machine = session.exec(query).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

# --- Command Execution API ---

from .models import Command

class CommandCreate(SQLModel):
    command: str

class CommandUpdate(SQLModel):
    output: str
    status: str

@app.post("/api/machines/{machine_id}/command", response_model=Command)
def create_command(machine_id: int, cmd_data: CommandCreate, session: Session = Depends(get_session)):
    machine = session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    cmd = Command(
        machine_id=machine_id,
        command=cmd_data.command,
        status="pending"
    )
    session.add(cmd)
    session.commit()
    session.refresh(cmd)
    return cmd

@app.get("/api/machines/{machine_id}/commands/pending", response_model=List[Command])
def get_pending_commands(machine_id: int, session: Session = Depends(get_session)):
    # Find machine by ID first to ensure it exists (optional but good practice)
    # Actually, agent knows its hostname usually. Let's assume agent sends hostname query param or just ID if it knows it.
    # For now, let's use machine_id as agent should know it from initial handshake or config.
    # UPDATE: Agent currently doesn't store ID. It only knows hostname.
    # Let's support hostname lookup for pending commands to make it easier for agent.
    # But for now, we'll implement by ID and see if we need hostname support.
    
    statement = select(Command).where(Command.machine_id == machine_id).where(Command.status == "pending")
    commands = session.exec(statement).all()
    return commands

# Alternative endpoint for Agent to poll by Hostname
@app.get("/api/commands/pending", response_model=List[Command])
def get_pending_commands_by_hostname(hostname: str, session: Session = Depends(get_session)):
    statement = select(Machine).where(Machine.hostname == hostname)
    machine = session.exec(statement).first()
    if not machine:
        return []
    
    cmd_stmt = select(Command).where(Command.machine_id == machine.id).where(Command.status == "pending")
    commands = session.exec(cmd_stmt).all()
    return commands

@app.post("/api/commands/{command_id}/result", response_model=Command)
def update_command_result(command_id: int, result: CommandUpdate, session: Session = Depends(get_session)):
    cmd = session.get(Command, command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd.output = result.output
    cmd.status = result.status
    cmd.executed_at = datetime.utcnow()
    
    session.add(cmd)
    session.commit()
    session.refresh(cmd)
    return cmd

@app.get("/api/commands/{command_id}", response_model=Command)
def get_command_status(command_id: int, session: Session = Depends(get_session)):
    cmd = session.get(Command, command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    return cmd

class ServiceAction(SQLModel):
    action: str # start, stop, restart

@app.post("/api/machines/{machine_id}/services/{service_name}/action", response_model=Command)
def control_service(machine_id: int, service_name: str, action_data: ServiceAction, session: Session = Depends(get_session)):
    machine = session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
        
    action = action_data.action.lower()
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    # Generate PowerShell command
    # Using -Force to ensure it happens
    if action == "start":
        ps_command = f"Start-Service -Name '{service_name}'"
    elif action == "stop":
        ps_command = f"Stop-Service -Name '{service_name}' -Force"
    elif action == "restart":
        ps_command = f"Restart-Service -Name '{service_name}' -Force"
        
    # Queue Command
    cmd = Command(
        machine_id=machine_id,
        command=ps_command,
        status="pending"
    )
    session.add(cmd)
    session.commit()
    session.refresh(cmd)
    return cmd

@app.get("/api/stats")
def read_stats(session: Session = Depends(get_session)):
    machines = session.exec(select(Machine)).all()
    total = len(machines)
    # Basic stats
    os_counts = {}
    for m in machines:
        os = m.os_info or "Unknown"
        os_counts[os] = os_counts.get(os, 0) + 1
        
    return {
        "total_machines": total,
        "os_distribution": os_counts
    }

# --- Authentication ---
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .auth import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import JWTError, jwt
from .auth import SECRET_KEY, ALGORITHM
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Modify startup to create admin user
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Create default admin if not exists (handle race condition)
    from .database import engine
    try:
        with Session(engine) as session:
            statement = select(User).where(User.username == "admin")
            user = session.exec(statement).first()
            if not user:
                hashed_pwd = get_password_hash("admin")
                admin_user = User(username="admin", hashed_password=hashed_pwd, role="admin")
                session.add(admin_user)
                session.commit()
                print("Created default admin user (admin/admin)")
    except Exception as e:
        print(f"Admin user creation skipped (likely exists): {e}")

# Mount static files for frontend (Must be last)
import os
from fastapi.staticfiles import StaticFiles # Added this import
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dist")

if os.path.exists(dist_path):
    app.mount("/dist", StaticFiles(directory=dist_path), name="dist")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
