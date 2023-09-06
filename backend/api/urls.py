from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

router = DefaultRouter()

router.register("recipes", views.RecipeViewSet, basename="recipes")
router.register("tags", views.TagViewSet, basename="tags")
router.register("users", views.SubscriptionViewSet, basename="subscription")
router.register("ingredients", views.IngredientViewSet, basename="ingredients")


urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
