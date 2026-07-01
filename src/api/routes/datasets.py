"""评测集管理 API"""

from __future__ import annotations
import json
import uuid

from fastapi import APIRouter, HTTPException

from src.models.dataset import Dataset, TestCase, DatasetImportRequest

router = APIRouter()

# 内存存储（生产环境替换为数据库）
_datasets: dict[str, Dataset] = {}


@router.get("/", summary="获取所有评测集")
async def list_datasets():
    return list(_datasets.values())


@router.get("/{dataset_id}", summary="获取单个评测集详情")
async def get_dataset(dataset_id: str):
    ds = _datasets.get(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="评测集不存在")
    return ds


@router.post("/", summary="创建评测集")
async def create_dataset(dataset: Dataset):
    if not dataset.id:
        dataset.id = str(uuid.uuid4())[:8]
    _datasets[dataset.id] = dataset
    return dataset


@router.post("/import", summary="导入评测集（JSON/CSV）")
async def import_dataset(req: DatasetImportRequest):
    dataset_id = str(uuid.uuid4())[:8]
    test_cases = []

    if req.format == "json":
        try:
            raw = json.loads(req.content)
            items = raw if isinstance(raw, list) else raw.get("test_cases", [])
            for item in items:
                test_cases.append(TestCase(
                    id=item.get("id", str(uuid.uuid4())[:8]),
                    input_text=item["input_text"],
                    expected_output=item.get("expected_output"),
                    category=item.get("category", "general"),
                    tags=item.get("tags", []),
                ))
        except (json.JSONDecodeError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")
    else:
        raise HTTPException(status_code=400, detail=f"暂不支持 {req.format} 格式")

    dataset = Dataset(
        id=dataset_id,
        name=req.name,
        description=req.description,
        test_cases=test_cases,
    )
    _datasets[dataset_id] = dataset
    return {"id": dataset_id, "size": len(test_cases)}


@router.delete("/{dataset_id}", summary="删除评测集")
async def delete_dataset(dataset_id: str):
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail="评测集不存在")
    del _datasets[dataset_id]
    return {"deleted": dataset_id}
