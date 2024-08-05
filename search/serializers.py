from rest_framework import serializers
from .models import Member, Product ,  Bid , WishList , ProductHistory 
from django.core.exceptions import ValidationError


class PayStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ['product_id', 'pay_status']


#이거 바꿔야하네
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['member_id', 'name', 'phone_num', 'address', 'email', 'mem_status']

    def validate_email(self, value):
        # 이메일에 '@' 문자가 포함되어 있는지 확인
        if '@' not in value:
            raise serializers.ValidationError("A valid email must contain '@'.")

        # 동일한 이메일이 데이터베이스에 이미 존재하는지 확인
        # 현재 인스턴스(수정 중인 멤버)의 이메일과 동일하면 검사를 생략
        if self.instance and self.instance.email == value:
            return value

        if Member.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")

        return value



class ProductHistorySerializer(serializers.ModelSerializer):
    bid_member_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductHistory
        fields = [
            'product_id', 'register_member_id', 'category', 'product_name', 'start_date',
            'end_date', 'last_bid_date', 'term_price', 'start_price', 'end_price', 
            'bid_member_name', 'num_bid', 'auction_status', 'file_count', 
            'product_info', 'view_num', 'pay_status'
        ]

    def get_bid_member_name(self, obj):
        if obj.award_member_id is None or obj.award_member_id.member_id == 56:
            return " "
        return obj.award_member_id.name


#아래 기존    
class CreateProjectSerializer(serializers.ModelSerializer):
    register_member_id = serializers.SerializerMethodField()
    bid_member_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'  # 모든 필드를 포함하도록 설정
        #fields = ['category', 'product_name', 'start_price', 'term_price', 'product_info', 'register_member_id', 'bid_member_id', 'file_count']
        read_only_fields = ('file_count',)  # file_count 필드를 읽기 전용으로 설정

    def get_register_member_id(self, obj):
        return obj.register_member.member_id if obj.register_member else None

    def get_bid_member_id(self, obj):
        return obj.bid_member.name if obj.bid_member else None 




class ProductSerializer(serializers.ModelSerializer):
    register_member = serializers.CharField(source='register_member.member_id', read_only=True)
    bid_member = serializers.CharField(source='bid_member.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_register_member(self, obj):
        return obj.register_member.member_id if obj.register_member else None

    def get_bid_member(self, obj):
        return obj.bid_member.name if obj.bid_member else None 






    
class WishProductSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.product_id')  # product_id 필드를 올바르게 참조

    class Meta:
        model = WishList
        fields = ['product_id']  # product_id만 포함
        #아래 수정

class GetAllWishListSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Product 정보를 포함시키기 위해 nested serializer 사용

    class Meta:
        model = WishList
        fields = ['member', 'product']

class WishListSerializer(serializers.ModelSerializer):
    member_id = serializers.IntegerField(write_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishList
        fields = ['member_id', 'product_id', 'member', 'product']
        read_only_fields = ['member', 'product']

    def create(self, validated_data):
        member_id = validated_data.pop('member_id')
        product_id = validated_data.pop('product_id')
        member = Member.objects.get(member_id=member_id)
        product = Product.objects.get(product_id=product_id)
        wishlist = WishList.objects.create(member=member, product=product, **validated_data)
        return wishlist



    
class BidSerializer(serializers.ModelSerializer):
    bid_product_name = serializers.CharField(source='bid_product.product_name', read_only=True)

    class Meta:
        model = Bid
        fields = ['bid_product_id', 'bid_product_name', 'bid_member_id', 'bid_price', 'bid_date'] 
