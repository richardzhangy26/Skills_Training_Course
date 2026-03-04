"""
数据类型定义 - 使用Pydantic进行数据验证
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """维度得分"""
    name: str = Field(..., description="维度名称")
    score: float = Field(..., description="得分")
    full_score: int = Field(..., description="满分")
    details: Optional[str] = Field(None, description="详细评价")


class EvaluationReport(BaseModel):
    """评测报告"""
    task_id: str = Field(..., description="任务ID")
    total_score: float = Field(..., description="总分")
    level: str = Field(..., description="等级：优秀/良好/合格/不合格")
    dimensions: List[DimensionScore] = Field(..., description="各维度得分")
    summary: str = Field(..., description="评价总结")
    evaluated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    dialogue_file: Optional[str] = Field(None, description="对话文件路径")


class DialogueMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色：student/ai/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[str] = Field(None, description="时间戳")


class DialogueStage(BaseModel):
    """对话阶段"""
    stage_id: str = Field(..., description="阶段ID")
    stage_name: str = Field(..., description="阶段名称")
    messages: List[DialogueMessage] = Field(default_factory=list, description="对话消息列表")


class DialogueMetadata(BaseModel):
    """对话元数据"""
    task_id: Optional[str] = Field(None, description="任务ID")
    profile: Optional[str] = Field(None, description="学生画像")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    total_rounds: Optional[int] = Field(None, description="总轮数")


class DialogueData(BaseModel):
    """对话数据"""
    metadata: DialogueMetadata = Field(default_factory=DialogueMetadata)
    stages: List[DialogueStage] = Field(default_factory=list, description="对话阶段列表")
    raw_text: Optional[str] = Field(None, description="原始文本内容")


class TeacherDocument(BaseModel):
    """教师文档"""
    raw_text: str = Field(..., description="原始文本")
    teaching_objectives: List[str] = Field(default_factory=list, description="教学目标")
    key_points: List[str] = Field(default_factory=list, description="知识点列表")
    workflow: Optional[List[str]] = Field(None, description="教学流程")
    scoring_standard: Optional[str] = Field(None, description="评分标准")


class EvaluatorConfig(BaseModel):
    """评测配置"""
    api_key: str = Field(..., description="API密钥")
    api_url: str = Field(..., description="API地址")
    model: str = Field(..., description="模型名称")
    max_concurrent: int = Field(3, description="最大并发数")
    timeout: int = Field(60, description="超时时间（秒）")
    temperature: float = Field(0.3, description="温度参数")


class BatchEvaluationReport(BaseModel):
    """批量评测报告"""
    total_files: int = Field(..., description="文件总数")
    avg_score: float = Field(..., description="平均分")
    score_distribution: Dict[str, int] = Field(..., description="分数分布")
    individual_reports: List[EvaluationReport] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
