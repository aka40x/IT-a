from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

app = FastAPI(title="Mini Test Session 09")

flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled"}
]


class FlightCreate(BaseModel):
    flight_number: str = Field(..., min_length=5, max_length=10)
    destination: str = Field(..., min_length=1)
    available_seats: int = Field(..., ge=1)


def find_flight_by_number(flight_number: str):
    for flight in flights_db:
        if flight["flight_number"] == flight_number:
            return flight
    return None


def find_flight_by_id(flight_id: int):
    for flight in flights_db:
        if flight["id"] == flight_id:
            return flight
    return None


def get_next_id():
    if not flights_db:
        return 1
    return max(flight["id"] for flight in flights_db) + 1


def build_envelope(status_code: int, message: str, data, error, path: str):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "path": path
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message")
        error = detail.get("error")
    else:
        message = str(detail)
        error = None

    return JSONResponse(
        status_code=exc.status_code,
        content=build_envelope(exc.status_code, message, None, error, request.url.path)
    )


@app.get("/flights")
async def get_flights(request: Request, status: str = Query(None)):
    if status:
        result = [flight for flight in flights_db if flight["status"] == status]
    else:
        result = flights_db

    return JSONResponse(
        status_code=200,
        content=build_envelope(200, "Lấy danh sách chuyến bay thành công!", result, None, request.url.path)
    )


@app.post("/flights")
async def create_flight(flight: FlightCreate, request: Request):
    if find_flight_by_number(flight.flight_number):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Lỗi: Số hiệu chuyến bay này đã tồn tại trên hệ thống điều hành!",
                "error": "ERR-AIR-01: Flight number conflict in current active schedule database."
            }
        )

    new_flight = {
        "id": get_next_id(),
        "flight_number": flight.flight_number,
        "destination": flight.destination,
        "available_seats": flight.available_seats,
        "status": "scheduled",
        "created_at": datetime.now().isoformat()
    }
    flights_db.append(new_flight)

    response_data = {
        "id": new_flight["id"],
        "flight_number": new_flight["flight_number"],
        "destination": new_flight["destination"],
        "available_seats": new_flight["available_seats"],
        "status": new_flight["status"]
    }

    return JSONResponse(
        status_code=201,
        content=build_envelope(201, "Khởi tạo chuyến bay mới thành công!", response_data, None, request.url.path)
    )


@app.delete("/flights/{flight_id}")
async def delete_flight(flight_id: int, request: Request):
    flight = find_flight_by_id(flight_id)
    if not flight:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Lỗi: Không tìm thấy mã chuyến bay yêu cầu để hủy!",
                "error": "ERR-AIR-02: Target flight ID is missing from system scope."
            }
        )

    flights_db.remove(flight)

    return JSONResponse(
        status_code=200,
        content=build_envelope(200, "Hủy chuyến bay thành công!", None, None, request.url.path)
    )
