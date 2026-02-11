from sqlmodel import Session, select
from database import engine
from models import Service, Machine

def check_services():
    with open("db_verify_result.txt", "w") as f:
        try:
            with Session(engine) as session:
                machines = session.exec(select(Machine)).all()
                f.write(f"Total Machines: {len(machines)}\n")
                
                for m in machines:
                    f.write(f"Machine: {m.hostname}\n")
                    services = session.exec(select(Service).where(Service.machine_id == m.id)).all()
                    f.write(f"  Service Count: {len(services)}\n")
                    if len(services) > 0:
                        f.write(f"  First Service: {services[0].name} - {services[0].status}\n")
                    else:
                        f.write("  NO SERVICES FOUND\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    try:
        from sqlalchemy import inspect
        insp = inspect(engine)
        print(f"Tables in DB: {insp.get_table_names()}", flush=True)
        check_services()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
