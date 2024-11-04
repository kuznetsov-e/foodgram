from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import SubscriptionViewSet, UserAvatarUpdateView
from .views import IngredientViewset, RecipeViewset, TagViewset

router = DefaultRouter()

router.register('ingredients', IngredientViewset, basename='ingredient')
router.register('tags', TagViewset, basename='tag')
router.register('recipes', RecipeViewset, basename='recipe')
router.register('users', SubscriptionViewSet, basename='subscription')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', UserAvatarUpdateView.as_view(),
         name='user-avatar'),
]
