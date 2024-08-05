# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.core.validators import MinValueValidator


class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    phone_num = models.CharField(max_length=12, null=False)
    address = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=100, null=False)
    mem_status = models.PositiveSmallIntegerField(null=False)
    member_string = models.CharField(max_length=100)  

    class Meta:
        managed = True
        db_table = 'member'



        
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    register_member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='registered_products')
    category = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    last_bid_date = models.DateTimeField(null=True, blank=True)
    term_price = models.PositiveIntegerField()
    start_price = models.PositiveIntegerField()
    highest_price = models.PositiveIntegerField()
    bid_member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True, default=56, related_name='bidded_products') #,default=0)
    num_bid = models.PositiveIntegerField(default=0)
    auction_status = models.PositiveSmallIntegerField(default=1)
    file_count = models.IntegerField(null=True, default=0)
    product_info = models.CharField(max_length=1023)
    view_num = models.PositiveIntegerField(default=0)

    class Meta:
        managed=True
        db_table = 'product'
        constraints = [
            models.CheckConstraint(check=Q(start_date__lt=F('end_date')), name='chk_start_end_date'),
            models.CheckConstraint(check=Q(start_date__lte=F('last_bid_date')), name='chk_start_last_bid_date'),
            models.CheckConstraint(check=Q(last_bid_date__lte=F('end_date')), name='chk_last_bid_end_date'),
            models.CheckConstraint(check=Q(start_price__lte=F('highest_price')), name='chk_start_highest_price'),
            models.CheckConstraint(check=~Q(register_member=F('bid_member')), name='chk_register_bid_member_id')
        ]




class ProductHistory(models.Model):
    product_id = models.PositiveIntegerField(primary_key=True)
    register_member_id = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name='product_histories_registered', db_column='register_member_id'
    )
    category = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    last_bid_date = models.DateTimeField(null=True, blank=True)
    term_price = models.PositiveIntegerField()
    start_price = models.PositiveIntegerField()
    end_price = models.PositiveIntegerField(null=True, blank=True)
    award_member_id = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_histories_awarded', db_column='award_member_id'
    )
    num_bid = models.PositiveIntegerField(default=0)
    auction_status = models.PositiveSmallIntegerField()
    file_count = models.PositiveSmallIntegerField()
    product_info = models.CharField(max_length=1023)
    view_num = models.PositiveIntegerField(default=0) 
    pay_status = models.PositiveSmallIntegerField(default=0)   # 지금 넣는중

    class Meta:
        db_table = 'product_history'




class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    bid_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bids')
    bid_member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='bids')
    bid_price = models.PositiveIntegerField()
    bid_date = models.DateTimeField()
    # transaction_id = models.CharField(max_length=21)
    transaction_id = models.CharField(max_length=21)
    bid_result=models.CharField(max_length=50)
    is_success = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'bid'





class WishList(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, db_column='member_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')

    class Meta:
        managed = True
        db_table = 'wish_list'
        unique_together = (('member', 'product'),)
        






