from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd

app = FastAPI()

DATA_DIR = Path(r"D:\我\pp_quotes\data")


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Portfolio Performance Quote Server"
    }


@app.get("/quotes/{fund_code}")
def get_quotes(fund_code: str):
    """
    接收格式如: 33_000217 或 SH_600031 的代码
    内部自动转换为通达信的完整文件名进行精准匹配
    """
    # =========================================================
    # 核心修改：将 URL 中的下划线 _ 还原为文件名中的 #
    # =========================================================
    real_file_name = fund_code.replace("_", "#")
    csv_path = DATA_DIR / f"{real_file_name}.csv"
    
    # 精准匹配，绝无重复冲突风险
    if not csv_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Quote file '{real_file_name}.csv' not found. Please check your market prefix."
        )

    try:
        # 读取数据
        df = pd.read_csv(csv_path)

        if "日期" not in df.columns or "close" not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="CSV file missing required columns ('日期' or 'close')"
            )

        # 构造 Portfolio Performance 期望的数据结构
        df_pp = pd.DataFrame({
            "date": df["日期"].astype(str),
            "close": df["close"].astype(float),
            "value": df["close"].astype(float)
        })
        
        # 高性能转换为字典列表
        result = df_pp.to_dict(orient="records")

        return JSONResponse(content={
            "isin": fund_code, # 返回请求时的代码
            "data": result
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))