import asyncio
import logging
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.client import ServiceError, client
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - [{settings.service_name}] - %(message)s",
)
logger = logging.getLogger(settings.service_name)

app = FastAPI(
    title="SmartFarm Web Gateway",
    description="Server-rendered browser application that composes the SmartFarm APIs.",
    version="2.0.0",
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def render(request: Request, template: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"request": request, "settings": settings, **context},
    )


def redirect_with_message(path: str, message: str, error: bool = False):
    flag = "error" if error else "message"
    separator = "&" if "?" in path else "?"
    return RedirectResponse(
        url=f"{path}{separator}{flag}={quote_plus(message)}", status_code=status.HTTP_303_SEE_OTHER
    )


async def health(service: str, url: str) -> dict:
    try:
        data = await client.get(service, f"{url}/health")
        return {"name": service, "online": data.get("status") == "healthy", "data": data}
    except ServiceError as exc:
        return {"name": service, "online": False, "data": {"status": "offline", "detail": exc.detail}}


async def get_farmers():
    return await client.get("user-service", f"{settings.user_service_url}/farmers")


async def get_farms():
    return await client.get("farm-service", f"{settings.farm_service_url}/farms")


@app.get("/health", tags=["Health"])
async def gateway_health():
    services = await asyncio.gather(
        health("user-service", settings.user_service_url),
        health("farm-service", settings.farm_service_url),
        health("monitoring-service", settings.monitoring_service_url),
    )
    online = all(item["online"] for item in services)
    return {"status": "healthy" if online else "degraded", "service": settings.service_name, "services": services}


@app.get("/", name="dashboard")
async def dashboard(request: Request):
    farmers, farms, services = await asyncio.gather(
        get_farmers(),
        get_farms(),
        asyncio.gather(
            health("user-service", settings.user_service_url),
            health("farm-service", settings.farm_service_url),
            health("monitoring-service", settings.monitoring_service_url),
        ),
        return_exceptions=True,
    )
    errors = [value.detail for value in (farmers, farms) if isinstance(value, ServiceError)]
    return render(
        request,
        "dashboard.html",
        title="Command Center",
        farmers=[] if isinstance(farmers, Exception) else farmers,
        farms=[] if isinstance(farms, Exception) else farms,
        services=[] if isinstance(services, Exception) else services,
        error=" | ".join(errors) if errors else None,
    )


@app.get("/farmers")
async def farmers_page(request: Request):
    try:
        farmers = await get_farmers()
        error = None
    except ServiceError as exc:
        farmers, error = [], exc.detail
    return render(request, "farmers/list.html", title="Farmer Registry", farmers=farmers, error=error)


@app.get("/farmers/new")
async def new_farmer_page(request: Request):
    return render(request, "farmers/form.html", title="Register Farmer", error=None)


@app.post("/farmers")
async def create_farmer(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str | None = Form(None),
):
    try:
        await client.post(
            "user-service",
            f"{settings.user_service_url}/farmers",
            {"name": name, "email": email, "password": password, "phone": phone or None},
        )
        return redirect_with_message("/farmers", "Farmer registered successfully.")
    except ServiceError as exc:
        return redirect_with_message("/farmers/new", exc.detail, error=True)


@app.get("/farmers/{farmer_id}")
async def farmer_detail(request: Request, farmer_id: int):
    try:
        farmer = await client.get("user-service", f"{settings.user_service_url}/farmers/{farmer_id}")
        farms = [farm for farm in await get_farms() if farm["farmer_id"] == farmer_id]
        return render(request, "farmers/detail.html", title=farmer["name"], farmer=farmer, farms=farms, error=None)
    except ServiceError as exc:
        return render(request, "errors/service.html", title="Farmer unavailable", error=exc.detail)


@app.get("/farms")
async def farms_page(request: Request):
    try:
        farms, farmers = await asyncio.gather(get_farms(), get_farmers())
        error = None
    except ServiceError as exc:
        farms, farmers, error = [], [], exc.detail
    farmer_names = {farmer["id"]: farmer["name"] for farmer in farmers}
    return render(request, "farms/list.html", title="Farm & Crop Registry", farms=farms, farmer_names=farmer_names, error=error)


@app.get("/farms/new")
async def new_farm_page(request: Request):
    try:
        farmers = await get_farmers()
        error = None
    except ServiceError as exc:
        farmers, error = [], exc.detail
    return render(request, "farms/form.html", title="Create Farm", farmers=farmers, error=error)


@app.post("/farms")
async def create_farm(
    farmer_id: int = Form(...),
    farm_name: str = Form(...),
    location: str = Form(...),
    area_acres: float = Form(...),
):
    try:
        await client.post(
            "farm-service",
            f"{settings.farm_service_url}/farms",
            {"farmer_id": farmer_id, "farm_name": farm_name, "location": location, "area_acres": area_acres},
        )
        return redirect_with_message("/farms", "Farm created successfully.")
    except ServiceError as exc:
        return redirect_with_message("/farms/new", exc.detail, error=True)


@app.get("/farms/{farm_id}")
async def farm_detail(request: Request, farm_id: int):
    try:
        farm = await client.get("farm-service", f"{settings.farm_service_url}/farms/{farm_id}")
        farmer = await client.get("user-service", f"{settings.user_service_url}/farmers/{farm['farmer_id']}")
        return render(request, "farms/detail.html", title=farm["farm_name"], farm=farm, farmer=farmer, error=None)
    except ServiceError as exc:
        return render(request, "errors/service.html", title="Farm unavailable", error=exc.detail)


@app.get("/farms/{farm_id}/crops/new")
async def new_crop_page(request: Request, farm_id: int):
    try:
        farm = await client.get("farm-service", f"{settings.farm_service_url}/farms/{farm_id}")
        return render(request, "farms/crop-form.html", title="Add Crop", farm=farm, error=None)
    except ServiceError as exc:
        return render(request, "errors/service.html", title="Farm unavailable", error=exc.detail)


@app.post("/farms/{farm_id}/crops")
async def create_crop(
    farm_id: int,
    crop_name: str = Form(...),
    crop_type: str = Form(...),
    sowing_date: str = Form(...),
    expected_harvest_date: str = Form(...),
    crop_status: str = Form("Sown"),
):
    try:
        await client.post(
            "farm-service",
            f"{settings.farm_service_url}/farms/{farm_id}/crops",
            {
                "crop_name": crop_name,
                "crop_type": crop_type,
                "sowing_date": sowing_date,
                "expected_harvest_date": expected_harvest_date,
                "status": crop_status,
            },
        )
        return redirect_with_message(f"/farms/{farm_id}", "Crop added to farm.")
    except ServiceError as exc:
        return redirect_with_message(f"/farms/{farm_id}/crops/new", exc.detail, error=True)


async def monitoring_data(farm_id: int):
    async def optional(path: str):
        try:
            return await client.get("monitoring-service", f"{settings.monitoring_service_url}{path}")
        except ServiceError as exc:
            if exc.status_code == 404:
                return None
            raise

    latest, summary, readings = await asyncio.gather(
        optional(f"/readings/{farm_id}/latest"),
        client.get("monitoring-service", f"{settings.monitoring_service_url}/readings/{farm_id}/summary"),
        client.get("monitoring-service", f"{settings.monitoring_service_url}/readings/{farm_id}"),
    )
    return {"latest": latest, "summary": summary, "readings": readings}


@app.get("/monitoring")
async def monitoring_page(request: Request, farm_id: int | None = Query(None)):
    try:
        farms = await get_farms()
        data = await monitoring_data(farm_id) if farm_id else None
        error = None
    except ServiceError as exc:
        farms, data, error = [], None, exc.detail
    return render(request, "monitoring/index.html", title="Field Monitoring", farms=farms, selected_farm_id=farm_id, data=data, error=error)


@app.get("/monitoring/history")
async def monitoring_history(request: Request, farm_id: int | None = Query(None)):
    try:
        farms = await get_farms()
        data = await monitoring_data(farm_id) if farm_id else None
        error = None
    except ServiceError as exc:
        farms, data, error = [], None, exc.detail
    return render(request, "monitoring/history.html", title="Reading History", farms=farms, selected_farm_id=farm_id, data=data, error=error)


@app.get("/monitoring/readings/new")
async def new_reading_page(request: Request):
    try:
        farms = await get_farms()
        error = None
    except ServiceError as exc:
        farms, error = [], exc.detail
    return render(request, "monitoring/form.html", title="Record Sensor Reading", farms=farms, error=error)


@app.post("/monitoring/readings")
async def create_reading(
    farm_id: int = Form(...),
    sensor_id: str = Form(...),
    temperature: float = Form(...),
    humidity: float = Form(...),
    soil_moisture: float = Form(...),
    rainfall: float = Form(...),
    battery: int | None = Form(None),
    signal_strength: int | None = Form(None),
):
    extra = {key: value for key, value in {"battery": battery, "signal_strength": signal_strength}.items() if value is not None}
    payload = {
        "farm_id": farm_id,
        "sensor_id": sensor_id,
        "temperature": temperature,
        "humidity": humidity,
        "soil_moisture": soil_moisture,
        "rainfall": rainfall,
        "additional_data": extra or None,
    }
    try:
        await client.post("monitoring-service", f"{settings.monitoring_service_url}/readings", payload)
        return redirect_with_message(f"/monitoring?farm_id={farm_id}", "Sensor reading stored in MongoDB.")
    except ServiceError as exc:
        return redirect_with_message("/monitoring/readings/new", exc.detail, error=True)


@app.get("/ajax/monitoring/{farm_id}")
async def monitoring_ajax(farm_id: int):
    try:
        return JSONResponse(await monitoring_data(farm_id))
    except ServiceError as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
