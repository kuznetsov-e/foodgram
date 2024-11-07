from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from .views import IngredientViewset, RecipeViewset, TagViewset

router = DefaultRouter()

router.register('ingredients', IngredientViewset, basename='ingredient')
router.register('tags', TagViewset, basename='tag')
router.register('recipes', RecipeViewset, basename='recipe')
router.register('users', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
