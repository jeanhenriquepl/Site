from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

class Software(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    version: Optional[str] = None
    publisher: Optional[str] = None
    machine_id: Optional[int] = Field(default=None, foreign_key="machine.id")
    machine: Optional["Machine"] = Relationship(back_populates="softwares")



class InventoryReport(SQLModel):
    hostname: str
    client_code: Optional[str] = "DEFAULT"
    ip_address: Optional[str]
    os_info: Optional[str]
    processor: Optional[str]
    ram_gb: Optional[float]
    disk_gb: Optional[float]
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Metrics
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    
    softwares: List[dict] = []
    services: List[dict] = []



class SoftwareRead(SQLModel):
    id: int
    name: str
    version: Optional[str] = None
    publisher: Optional[str] = None

class ServiceRead(SQLModel):
    id: int
    name: str
    display_name: Optional[str]
    status: str
    start_type: Optional[str]

class MachineBase(SQLModel):
    hostname: str = Field(index=True)
    client_code: str = Field(default="DEFAULT", index=True)
    ip_address: Optional[str] = None
    os_info: Optional[str] = None
    processor: Optional[str] = None
    ram_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Snapshot metrics (optional to keep in base, but useful for list view)
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    status: str = "online"
    alert_message: Optional[str] = None

class Command(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machine.id")
    command: str
    output: Optional[str] = None
    status: str = "pending" # pending, running, completed, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    
    machine: Optional["Machine"] = Relationship(back_populates="commands")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = "admin"

class Machine(MachineBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Real-time metrics
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    status: str = "online" # online, warning, critical, offline
    alert_message: Optional[str] = None
    
    softwares: List["Software"] = Relationship(back_populates="machine")
    services: List["Service"] = Relationship(back_populates="machine")
    commands: List["Command"] = Relationship(back_populates="machine")

class MachineRead(MachineBase):
    id: int
    softwares: List[SoftwareRead] = []
    services: List[ServiceRead] = []

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    display_name: Optional[str] = None
    status: str
    start_type: Optional[str] = None
    machine_id: Optional[int] = Field(default=None, foreign_key="machine.id")
    machine: Optional["Machine"] = Relationship(back_populates="services")
