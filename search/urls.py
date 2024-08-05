from django.conf import settings
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

# 스키마 뷰 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[AllowAny]
)

router = DefaultRouter()
router.register(r'product', ProductViewSet, basename='product')
router.register(r'product_noview', NoViewNumProductViewSet, basename='noviewproduct')
router.register(r'member', MemberViewSet, basename='member')

urlpatterns = [
    path('', include(router.urls)),
    path('pay_status/<int:product_id>/', PayStatusUpdateView.as_view(), name='pay_status_update'),
    path('searchall/', ProductAndHistorySearchView.as_view(), name='product_and_history_search'),
    path('pwishlist/<int:member_id>/', GetAllWishListAPIView.as_view(), name='wishlists'),
    path('biding/<int:member_id>/', RecentSuccessfulBidsView.as_view(), name='recent-successful-bids'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('product/category/<int:member_id>/', ProductViewSet.as_view({'get': 'list'}), name='product-list-by-member'), #여기 마지막에 ?category=가전제품
    path('product_history/member/<int:member_id>/', ProductHistoryByMemberAPIView.as_view(), name='product-history-by-member'),
    path('product_history/buyer/<int:buyer_id>/', ProductHistoryByMemberAPIView.as_view(), name='product-history-by-buyer'),
    path('product_history/<int:product_id>/', ProductHistoryByProductAPIView.as_view(), name='product_history_by_product'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('bid/<int:member_id>/', MemberRegisteredProductsAPIView.as_view(), name='member-bids'),
    path('wishlist/<int:member_id>/', WishListAPIView.as_view(), name='wishlist'),
    path('wishlist/', WishListCreateDeleteAPIView.as_view(), name='wishlist-manage'),
    path('redis/ranking/', SearchRankingView.as_view(), name='search-ranking'),
    path('redis/update/', UpdateSearchRankingView.as_view(), name='update-search-ranking'),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
