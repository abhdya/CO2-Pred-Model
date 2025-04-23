import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from typing import Dict, Optional

# Load models safely
def load_model(path):
    try:
        return joblib.load(path)
    except FileNotFoundError:
        return None

# Pre-load available models
models = {
    "BulkCarrier": load_model('ship_model_1.joblib'),
    "GasCarrier": load_model('ship_model_2.joblib'),
    "Tanker": load_model('ship_model_3.joblib'),
    "Containership": load_model('ship_model_4.joblib'),
    "RefrigeratedCargoCarrier": load_model('ship_model_6.joblib'),
    "RoRoCargoShipVehicleCarrier": load_model('ship_model_9.joblib'),
    "GeneralCargoShip": None,
    "CombinationCarrier": None,
    "HighSpeedCraft": None, 
    "RoRoCargoShip": None,
    "RoRoPassengerShip": None,
    "LNGCarrier": None,
    "CruisePassengerShip": None
}

app = FastAPI(title="CO2 Emissions Prediction API")

class FuelTypesModel(BaseModel):
    ME_MDO_MGO: Optional[int] = 0
    ME_HFO: Optional[int] = 0
    ME_LFO: Optional[int] = 0
    AE_Boiler_MDO_MGO: Optional[int] = 0
    AE_Boiler_HFO: Optional[int] = 0
    AE_Boiler_LFO: Optional[int] = 0
    
class InputData(BaseModel):
    ship_type: str
    Deadweight: float
    GrossTonnage: float
    SteamingTime: float
    Distance: float
    FuelTypes: Dict[str, int]

    model_config = {
        "json_schema_extra": {
            "example": {
                "ship_type": "BulkCarrier",
                "Deadweight": 10000.0,
                "GrossTonnage": 5000.0,
                "SteamingTime": 24.0,
                "Distance": 1000.0,
                "FuelTypes": {
                    "ME_MDO/MGO": 1,
                    "ME_HFO": 0,
                    "ME_LFO": 0,
                    "AE_Boiler_MDO/MGO": 1,
                    "AE_Boiler_HFO": 0,
                    "AE_Boiler_LFO": 0
                }
            }
        }
    }

# Allow all CORS (modify for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to the CO2 Emissions Prediction API"}

@app.post("/predict")
def predict(data: InputData):
    try:
        # Check if ship_type is supported
        if data.ship_type not in models:
            return {
                "error": f"Invalid ship type. Must be one of {list(models.keys())}"
            }

        model = models[data.ship_type]
        if model is None:
            return {
                "Ship Type": data.ship_type,
                "Predicted CO2 Emissions": None,
                "message": "No prediction model available for this ship type"
            }

        # Define the expected feature order
        expected_features = [
            "Deadweight",
            "GrossTonnage",
            "Distance",
            "SteamingTime",
            "ME_MDO/MGO",
            "ME_HFO",
            "ME_LFO",
            "AE_Boiler_MDO/MGO",
            "AE_Boiler_HFO",
            "AE_Boiler_LFO"
        ]

        # Build input in correct order
        input_dict = {
            "Deadweight": data.Deadweight,
            "GrossTonnage": data.GrossTonnage,
            "Distance": data.Distance,
            "SteamingTime": data.SteamingTime,
            "ME_MDO/MGO": data.FuelTypes.get("ME_MDO/MGO", 0),
            "ME_HFO": data.FuelTypes.get("ME_HFO", 0),
            "ME_LFO": data.FuelTypes.get("ME_LFO", 0),
            "AE_Boiler_MDO/MGO": data.FuelTypes.get("AE_Boiler_MDO/MGO", 0),
            "AE_Boiler_HFO": data.FuelTypes.get("AE_Boiler_HFO", 0),
            "AE_Boiler_LFO": data.FuelTypes.get("AE_Boiler_LFO", 0)
        }

        # Create DataFrame in the expected column order
        df = pd.DataFrame([[input_dict[feature] for feature in expected_features]],
                          columns=expected_features)

        # Make prediction
        prediction = model.predict(df)[0]

        return {
            "Ship Type": data.ship_type,
            "Predicted CO2 Emissions": round(float(prediction), 4)
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        excel_file = BytesIO(contents)
        df = pd.read_excel(excel_file, engine='openpyxl')
        excel_file.close()

        ship_names = df['SHIPNAME'].dropna().unique().tolist()
        return {"ship_names": ship_names}
    except Exception as e:
        return {"error": str(e)}

# Load Norbulk data
norbulk_df = pd.read_excel('Datasets/Norbulk_24_35.xlsx', engine='openpyxl')

ship_type_mapping = {
    1: "BulkCarrier",
    2: "GasCarrier",
    3: "Tanker",
    4: "Containership",
    5: "GeneralCargoShip",
    6: "RefrigeratedCargoCarrier",
    7: "CombinationCarrier",
    8: "HighSpeedCraft",
    9: "RoRoCargoShipVehicleCarrier",
    10: "RoRoCargoShip",
    11: "RoRoPassengerShip",
    12: "LNGCarrier",
    13: "CruisePassengerShip"
}

@app.get("/get-ship-types/")
def get_ship_types():
    try:
        ship_type_ids = norbulk_df['SHIPTYPEID_CII'].dropna().unique().tolist()
        ship_types = [
            {"id": int(id), "name": ship_type_mapping.get(int(id), f"Ship Type {id}")}
            for id in ship_type_ids
        ]
        return {"ship_types": ship_types}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get-ship-names/{ship_type}")
def get_ship_names(ship_type: str):
    try:
        ship_type_id = next(id for id, name in ship_type_mapping.items() if name == ship_type)
        ships = norbulk_df[norbulk_df['SHIPTYPEID_CII'] == ship_type_id]['SHIPNAME']
        ship_names = pd.Series(ships).dropna().unique().tolist()
        return {"ship_names": ship_names}
    except StopIteration:
        return {"error": f"Invalid ship type: {ship_type}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get-ship-data/{ship_name}")
def get_ship_data(ship_name: str):
    try:
        ship_data = norbulk_df[norbulk_df['SHIPNAME'] == ship_name]
        if ship_data.empty:
            return {"error": "Ship not found"}

        first_entry = ship_data.iloc[0]
        return {
            "deadweight": float(first_entry['DeadWeight']),
            "grosstonnage": float(first_entry['GrossTonnage'])
        }
    except Exception as e:
        return {"error": str(e)}
