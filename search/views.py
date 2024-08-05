from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status, viewsets
from .models import Member, Product  , Bid , WishList , ProductHistory 
from .serializers import MemberSerializer,  CreateProjectSerializer, ProductSerializer,  WishListSerializer, ProductHistorySerializer
from .serializers import WishProductSerializer, GetAllWishListSerializer ,PayStatusUpdateSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from django.views import View
from django.http import JsonResponse
from django.db import transaction
import boto3
import os
from django.conf import settings
import logging
from django.shortcuts import get_object_or_404
from django.utils.http import unquote
from .services import SearchService
from rest_framework.decorators import action
from django.db.models import Q, F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Max,OuterRef, Subquery
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
import datetime
import pytz

from rest_framework import serializers
from django.db import DatabaseError
from tempfile import SpooledTemporaryFile
from urllib.parse import quote_plus
import traceback
import urllib.parse

logger = logging.getLogger('django')






class ProductHistoryByProductAPIView(APIView):
    def get(self, request, product_id):
        # URL에서 product_id를 기반으로 ProductHistory 객체를 조회
        product_histories = ProductHistory.objects.filter(product_id=product_id)

        if product_histories.exists():
            # view_num을 1씩 증가시킴
            product_histories.update(view_num=F('view_num') + 1)

            # 직렬화 과정에서 다시 조회하여 최신 정보를 반영
            product_histories = ProductHistory.objects.filter(product_id=product_id)
            serializer = ProductHistorySerializer(product_histories, many=True)
            return Response(serializer.data)
        else:
            return Response({'message': 'No product history found for the given product ID.'}, status=status.HTTP_404_NOT_FOUND) 
        




class RecentSuccessfulBidsView(APIView):
    def get(self, request, member_id):
        # 서브쿼리를 통해 각 제품의 최신 입찰 날짜 찾기
        latest_bid_dates = Bid.objects.using('replica').filter(
            bid_member_id=member_id,
            is_success=1,
            bid_result='입찰 성공!'
        ).values('bid_product_id').annotate(
            latest_bid_date=Max('bid_date')
        ).values('latest_bid_date', 'bid_product_id')

        # 최신 입찰 날짜를 가진 입찰들을 가져오기
        latest_bids = Bid.objects.using('replica').filter(
            bid_member_id=member_id,
            is_success=1,
            bid_result='입찰 성공!',
            bid_date=Subquery(
                latest_bid_dates.filter(bid_product_id=OuterRef('bid_product_id')).values('latest_bid_date')[:1]
            )
        )

        # 결과 준비
        results = []
        for bid in latest_bids:
            try:
                product = Product.objects.using('replica').get(product_id=bid.bid_product_id)
                result = {
                    'product_id': product.product_id,
                    'product_name': product.product_name,
                    'highest_price': product.highest_price,
                    'bid_date': bid.bid_date,
                }
                results.append(result)
            except Product.DoesNotExist:
                continue

        return Response(results)
    
    

class GetAllWishListAPIView(APIView):
    def get(self, request, member_id):
        # 특정 멤버의 위시리스트에 담긴 제품 정보 가져오기
        wishlists = WishList.objects.filter(member_id=member_id).select_related('product')
        # 위시리스트 인스턴스를 직렬화
        serializer = GetAllWishListSerializer(wishlists, many=True)
        return Response(serializer.data)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


class UpdateSearchRankingView(APIView):
    def post(self, request):
        keyword = request.data.get("searchWord")
        if not keyword:
            return Response({"error": "searchWord is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        service = SearchService()
        service.handle_expired_keywords()  # 만료된 키를 처리
        result = service.update_search_ranking(keyword)
 



class ProductSearchView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Search results",
                schema=ProductSerializer(many=True)
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request):
        query = request.query_params.get('q', None)

        if query is not None:
            query = query.strip()
        
        if query:
            # Update search ranking in Redis with the original query (including spaces)
            service = SearchService()
            service.update_search_ranking(query)

            # Split the query by spaces
            words = query.split()

            # Dynamically build the query using Q objects
            query_filter = Q()
            for word in words:
                query_filter |= Q(product_name__icontains=word)
            
            # Add filter for end_date greater than current time
            query_filter &= Q(end_date__gt=timezone.now())

            # Retrieve the search results ordered by end_date ascending (using the replica database)
            queryset = Product.objects.using('replica').filter(query_filter).order_by('end_date')
            serializer = ProductSerializer(queryset, many=True)

            return Response(serializer.data)
        
        # If query is None or empty
        logger.debug("No valid query parameter provided")
        return Response({"error": "No query parameter provided or query is empty"}, status=status.HTTP_400_BAD_REQUEST)
    



class ProductAndHistorySearchView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Search results",
                examples={
                    "application/json": [
                        {
                            "type": "product",
                            "product_id": 1,
                            "product_name": "Example"
                        },
                        {
                            "type": "history",
                            "product_id": 1,
                            "product_name": "Example"
                        }
                    ]
                }
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request):
        query = request.query_params.get('q', None)

        if query is None or not query.strip():
            return Response({"error": "No query parameter provided or query is empty"}, status=status.HTTP_400_BAD_REQUEST)

        query = query.strip()
        
        # Update search ranking in Redis with the original query (including spaces)
        service = SearchService()
        service.update_search_ranking(query)

        # Split the query by spaces and build the query using Q objects
        words = query.split()
        product_query_filter = Q()
        history_query_filter = Q()
        for word in words:
            common_filter = Q(product_name__icontains=word)
            product_query_filter |= common_filter
            history_query_filter |= common_filter

        # Filter for current products
        product_query = Product.objects.using('replica').filter(product_query_filter & Q(end_date__gt=timezone.now())).order_by('end_date')
        # Filter for product history without end_date constraint
        history_query = ProductHistory.objects.using('replica').filter(history_query_filter).order_by('end_date')

        # Serialize the results
        product_serializer = ProductSerializer(product_query, many=True)
        history_serializer = ProductHistorySerializer(history_query, many=True)

        # Combine results and add type field
        results = [{'type': 'product', **item} for item in product_serializer.data] + \
                  [{'type': 'history', **item} for item in history_serializer.data]

        return Response(results)
    


class SearchRankingView(APIView):
    def get(self, request):
        service = SearchService()
        service.handle_expired_keywords()  # 만료된 키를 처리
        ranking_list = service.search_ranking_list()
        ranking_list_data = [{'keyword': search.keyword, 'score': search.score} for search in ranking_list]
        return Response(ranking_list_data, status=status.HTTP_200_OK)
    

class ProductCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    file_field = openapi.Parameter(
        'images', openapi.IN_FORM, description="Upload images",
        type=openapi.TYPE_FILE, required=True
    )

    @swagger_auto_schema(
        operation_description="Uploads a product and its images to the server and S3.",
        manual_parameters=[file_field],
        request_body=CreateProjectSerializer,
        responses={
            201: CreateProjectSerializer(many=False),
            400: 'Validation Error',
            500: 'Internal Server Error'
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            timezone.activate('Asia/Seoul')
            now = timezone.now()

            data = {
                'start_date': now,
                'end_date': now + timedelta(seconds=60),
                'highest_price': request.data.get('highest_price', request.data.get('start_price')),
                'bid_member': request.data.get('bid_member', 56),
                'category': request.data.get('category'),
                'product_name': request.data.get('product_name'),
                'term_price': request.data.get('term_price'),
                'start_price': request.data.get('start_price'),
                'product_info': request.data.get('product_info'),
                'register_member': request.data.get('register_member')
            }

            product_serializer = CreateProjectSerializer(data=data)
            if product_serializer.is_valid():
                product = product_serializer.save()
                images_data = request.FILES.getlist('images')
                image_limit = 6
                images_data = images_data[:image_limit]

                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )

                image_count = 0
                unsupported_files = []
                for image_index, image_data in enumerate(images_data, start=1):
                    ext = os.path.splitext(image_data.name)[1].lower()
                    if ext in ['.jpeg', '.jpg', '.png']:
                        file_ext = 'jpg'
                    elif ext in ['.mov', '.mp4', '.avi']:
                        file_ext = 'mov'
                    else:
                        unsupported_files.append(image_data.name)
                        logger.warning(f"Unsupported file type for {image_data.name}: {ext}")
                        continue

                    file_path = f'{product.product_id}/{image_index}.{file_ext}'
                    try:
                        with image_data.open('rb') as file_obj:
                            s3_client.upload_fileobj(file_obj, settings.AWS_STORAGE_BUCKET_NAME, file_path)
                        image_count += 1
                        # 성공한 로그 메시지 (주석 제거됨)
                        logger.info(f"물품등록 완료 - ID: {product.product_id}, 카테고리: {product.category}, 이름: {product.product_name}. 성공적으로 업로드된 파일 수: {image_count}")
                    except Exception as e:
                        logger.error(f"Error uploading {image_data.name} to S3: {str(e)}")
                        continue

                if unsupported_files:
                    logger.warning(f"Unsupported file types detected: {unsupported_files}")
                    return Response({'error': 'Unsupported file types', 'details': unsupported_files}, status=status.HTTP_400_BAD_REQUEST)

                product.file_count = image_count
                product.save()

                try:
                    response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=f'{product.product_id}/')
                    if 'Contents' in response:
                        logger.info(f"Files found in S3 for product")
                        
                    else:
                        logger.info(f"No files found in S3 for product {product.product_id}")
                except Exception as e:
                    logger.error(f"Error listing S3 objects for product {product.product_id}: {str(e)}")

                return Response(product_serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Validation errors: {product_serializer.errors}")
                return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            if 'images_data' in locals():
                for image_data in images_data:
                    if hasattr(image_data, 'close'):
                        try:
                            image_data.close()
                        except Exception as e:
                            logger.error(f"Error closing file {image_data.name}: {str(e)}")





class NoViewNumProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.using('replica').all().order_by('product_id')
        category_name = self.request.query_params.get('category', None)
        pid = self.request.query_params.get('pid', None)
        register_member_id = self.request.query_params.get('register_member_id', None)

        if category_name:
            category_name = unquote(category_name)
            queryset = queryset.filter(category=category_name)
            log_message = f"[{timezone.now()}] 카테고리 : {category_name} "
            logger.info(log_message, extra={
                'custom_message': log_message,
                'request_path': self.request.path,
                'timestamp': timezone.now().isoformat(),
                'category_name': category_name
            })

        if pid:
            queryset = queryset.filter(product_id=pid)
            log_message = f"[{timezone.now()}] Product ID : {pid} 조회"
            logger.info(log_message, extra={
                'custom_message': log_message,
                'request_path': self.request.path,
                'timestamp': timezone.now().isoformat(),
                'product_id': pid
            })

        if register_member_id:
            queryset = queryset.filter(register_member_id__member_id=register_member_id)

        queryset = queryset.filter(end_date__gt=timezone.now())
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)




class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.using('replica').all().order_by('product_id')
        category_name = self.request.query_params.get('category', None)
        pid = self.request.query_params.get('pid', None)
        register_member_id = self.request.query_params.get('register_member_id', None)

        log_messages = []

        if category_name:
            category_name = unquote(category_name)
            queryset = queryset.filter(category=category_name)
            log_messages.append(f"카테고리 : {category_name}")

        if pid:
            queryset = queryset.filter(product_id=pid)
            log_messages.append(f"Product ID : {pid} 조회")

        if register_member_id:
            queryset = queryset.filter(register_member_id__member_id=register_member_id)

        queryset = queryset.filter(end_date__gt=timezone.now())

        if log_messages:
            log_message = f"[{timezone.now()}] " + " - ".join(log_messages)
            logger.info(log_message, extra={
                'custom_message': log_message,
                'request_path': self.request.path,
                'timestamp': timezone.now().isoformat(),
            })

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DatabaseError as e:
            logger.error("Database connection failed", exc_info=True)
            return Response({'error': 'Database connection failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.view_num = F('view_num') + 1
            instance.save(using='default')  # 쓰기 작업은 기본 데이터베이스에 수행
            instance.refresh_from_db()

            # 카테고리 정보를 가져오기 위한 코드 추가
            category_name = instance.category if hasattr(instance, 'category') else 'Unknown'

            log_message = f"[{timezone.now()}] 카테고리 : {category_name} - Product ID : {instance.product_id} viewed"
            logger.info(log_message, extra={
                'custom_message': log_message,
                'request_path': request.path,
                'timestamp': timezone.now().isoformat(),
                'product_id': instance.product_id,
                'category_name': category_name
            })
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except DatabaseError as e:
            logger.error("Database connection failed", exc_info=True)
            return Response({'error': 'Database connection failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MemberRegisteredProductsAPIView(APIView):
    def get(self, request, member_id):
        # 멤버 ID에 따라 Product 객체를 필터링하고, 현재 시간보다 늦게 끝나는 상품만을 포함합니다.
        # 여기서는 멤버가 등록한 상품들만 조회합니다.
        products = Product.objects.using('replica').filter(
            register_member_id=member_id, 
            end_date__gt=timezone.now()
        )

        # 상품 객체 리스트를 직렬화합니다.
        serializer = ProductSerializer(products, many=True)

        # 직렬화된 데이터를 API 응답으로 반환합니다.
        return Response(serializer.data)



class WishListAPIView(APIView):
    def get(self, request, member_id):
        # 쿼리 파라미터에서 product_id 가져오기
        product_id = request.query_params.get('product_id')
        current_time = timezone.now()

        if product_id:
            # 특정 멤버의 위시리스트에서 특정 product_id만 필터링하고 제품 테이블과 조인
            wishlists = WishList.objects.using('replica').filter(
                member_id=member_id, 
                product_id=product_id,
                product__end_date__gt=current_time  # product 테이블의 end_date가 현재 시간보다 커야 함
            ).select_related('product')
        else:
            # 특정 멤버의 위시리스트에 담긴 모든 제품 정보 가져오기, 제품 테이블과 조인
            wishlists = WishList.objects.using('replica').filter(
                member_id=member_id,
                product__end_date__gt=current_time  # product 테이블의 end_date가 현재 시간보다 커야 함
            ).select_related('product')

        # WishList 인스턴스 전체를 직렬화
        serializer = WishProductSerializer(wishlists, many=True)
        product_ids = [entry['product_id'] for entry in serializer.data]
        return Response({'product_id': product_ids})


class WishListCreateDeleteAPIView(APIView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Unique identifier of the member'),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Unique identifier of the product'),
            },
            required=['member_id', 'product_id']
        ),
        responses={
            201: openapi.Response(description='Created', schema=WishListSerializer),
            400: openapi.Response(description='Bad request'),
            409: openapi.Response(description='Conflict'),
            404: openapi.Response(description='Not Found')
        }
    )
    def post(self, request):
        try:
            member_id = request.data['member_id']
            product_id = request.data['product_id']
        except KeyError:
            return Response({'error': 'member_id and product_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = Member.objects.using('replica').get(member_id=member_id)
            product = Product.objects.using('replica').get(product_id=product_id)
            wish_list, created = WishList.objects.using('default').get_or_create(member=member, product=product)

            if created:
                serializer = WishListSerializer(wish_list)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'WishList item already exists.'}, status=status.HTTP_409_CONFLICT)

        except Member.DoesNotExist:
            return Response({'error': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Unique identifier of the member'),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Unique identifier of the product'),
            },
            required=['member_id', 'product_id']
        ),
        responses={
            204: openapi.Response(description='No Content'),
            400: openapi.Response(description='Bad request'),
            404: openapi.Response(description='Not Found')
        }
    )
    def delete(self, request):
        try:
            member_id = request.data['member_id']
            product_id = request.data['product_id']
        except KeyError:
            return Response({'error': 'member_id and product_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wish_list = WishList.objects.using('replica').get(member__member_id=member_id, product__product_id=product_id)
            wish_list.delete(using='default')
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WishList.DoesNotExist:
            return Response({'message': 'Item not found in wishlist.'}, status=status.HTTP_404_NOT_FOUND)




class ProductHistoryByMemberAPIView(APIView):
    def get(self, request, member_id=None, buyer_id=None):
        logger.info(f"Fetching product histories for member_id={member_id} or buyer_id={buyer_id}")
        
        if member_id:
            product_histories = ProductHistory.objects.using('replica').filter(register_member_id=member_id)
            logger.info(f"Product histories for register_member_id={member_id}: {product_histories.count()}")
        elif buyer_id:
            product_histories = ProductHistory.objects.using('replica').filter(award_member_id=buyer_id)
            logger.info(f"Product histories for award_member_id={buyer_id}: {product_histories.count()}")
        else:
            return Response({'message': 'No valid identifier provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 빈 리스트를 반환하도록 serializer 처리 변경
        serializer = ProductHistorySerializer(product_histories, many=True)
        return Response(serializer.data)





class PayStatusUpdateView(APIView):
    def post(self, request, product_id):
        try:
            product_history = ProductHistory.objects.get(product_id=product_id)
        except ProductHistory.DoesNotExist:
            return Response({'error': 'Product history not found'}, status=status.HTTP_404_NOT_FOUND)
        
        product_history.pay_status = 1
        product_history.save()
        
        serializer = PayStatusUpdateSerializer(product_history)
        return Response(serializer.data, status=status.HTTP_200_OK)