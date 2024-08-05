import os
import requests
from django.utils import timezone
import logging

logger = logging.getLogger("django")

def transfer_products_to_history():
    from search.models import Product, ProductHistory, Member

    now = timezone.now()
    products_to_transfer = Product.objects.filter(end_date__lt=now)

    for product in products_to_transfer:
        if product.product_id == 0:
            continue  # Skip the product with an invalid ID
        register_member = product.register_member
        award_member = product.bid_member if product.bid_member else None

        # 로깅을 위한 정보 미리 저장
        product_id = product.product_id
        product_name = product.product_name
        end_date = product.end_date.isoformat()

        # ProductHistory 생성
        ProductHistory.objects.create(
            product_id=product_id,
            register_member_id=register_member,
            category=product.category,
            product_name=product_name,
            start_date=product.start_date,
            end_date=product.end_date,
            term_price=product.term_price,
            start_price=product.start_price,
            end_price=product.highest_price,
            award_member_id=award_member,
            num_bid=product.num_bid,
            auction_status=0,
            file_count=product.file_count,
            last_bid_date=product.last_bid_date,
            product_info=product.product_info,
            view_num=product.view_num,
            pay_status=0
        )

        # 로그 메시지 작성
        log_message = f"[{now}] 물품id: {product_id}, 물품이름: {product_name}의 경매가 종료"
        logger.info(log_message, extra={
            'custom_message': log_message,
            'timestamp': now.isoformat(),
            'product_id': product_id,
            'product_name': product_name,
            'end_date': end_date,
        })

        # Spring 서버에 API 요청 보내기
        api_url = os.getenv('SPRING_SERVER_URL') 
        if not api_url:
            logger.error("Spring server URL is not set in the environment variables.")
            continue

        headers = {'Content-Type': 'application/json'}
        payload = {'productId': product_id}

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()  # 요청이 실패하면 예외 발생
            logger.info(f"Successfully notified Spring server with product ID: {product_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to notify Spring server with product ID {product_id}: {str(e)}")
            if response:
                logger.error(f"Response Body: {response.text}")

        # Product 삭제는 마지막에 수행
        product.delete()

    logger.info("Transfer completed")
