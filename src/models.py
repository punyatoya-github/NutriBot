from pydantic import BaseModel, Field
from typing import List, Optional


class Recipe(BaseModel):
    title: str = Field(..., description="Recipe title")
    ingredients: List[str] = Field(..., description="List of ingredients required for the recipe")
    steps: List[str] = Field(
        default_factory=list,
        description="Cooking method as an ordered list of short steps (one action per step)",
    )
    instructions: str = Field(
        "",
        description="Optional single-string version of the cooking steps (kept for backwards compatibility)",
    )
    calorie_estimate: int = Field(..., description="Estimated calories per serving")
    cook_time_minutes: Optional[int] = Field(None, description="Total prep and cook time in minutes")
    servings: Optional[int] = Field(None, description="Number of servings the recipe makes")


class RecipeSuggestionOutput(BaseModel):
    recipes: List[Recipe] = Field(..., description="List of suggested recipes")


class VitaminInfo(BaseModel):
    name: str = Field(..., description="Name of the vitamin")
    percentage_dv: str = Field(..., description="Percentage of the Daily Value")


class MineralInfo(BaseModel):
    name: str = Field(..., description="Name of the mineral")
    amount: str = Field(..., description="Amount and unit of the mineral")


class NutrientBreakdown(BaseModel):
    protein: Optional[str] = Field(None, description="Total protein in grams, e.g. '32 g'")
    carbohydrates: Optional[str] = Field(None, description="Total carbohydrates in grams, e.g. '45 g'")
    fats: Optional[str] = Field(None, description="Total fat in grams, e.g. '18 g'")
    vitamins: List[VitaminInfo] = Field(default_factory=list, description="List of vitamins and their %DV")
    minerals: List[MineralInfo] = Field(default_factory=list, description="List of minerals and their amounts")


class FoodItem(BaseModel):
    name: str = Field(..., description="Identified food item")
    portion: Optional[str] = Field(None, description="Portion size of this item, e.g. '6 oz'")
    calories: Optional[int] = Field(None, description="Estimated calories for this item")


class NutrientAnalysisOutput(BaseModel):
    dish: Optional[str] = Field(None, description="Identified dish")
    portion_size: Optional[str] = Field(None, description="Portion size description")
    estimated_calories: Optional[int] = Field(None, description="Estimated total calories per portion")
    items: List[FoodItem] = Field(default_factory=list, description="Per-item calorie breakdown")
    nutrients: NutrientBreakdown = Field(default_factory=NutrientBreakdown, description="Detailed nutrient breakdown")
    health_score: Optional[int] = Field(None, description="Overall healthiness of the meal from 0 (poor) to 100 (excellent)")
    health_strengths: List[str] = Field(default_factory=list, description="2-4 short points on what is good about this meal")
    health_improvements: List[str] = Field(default_factory=list, description="2-4 short, actionable suggestions to improve the meal")
    health_evaluation: Optional[str] = Field(None, description="One-paragraph health evaluation summary")
