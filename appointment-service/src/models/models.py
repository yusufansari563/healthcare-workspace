from typing import Optional
import datetime
import decimal

from sqlalchemy import Column, DECIMAL, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, Table, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, DOUBLE, INTEGER, TINYINT
from sqlmodel import Field, Relationship, SQLModel

class PrismaMigrations(SQLModel, table=True):
    __tablename__ = '_prisma_migrations'

    id: str = Field(sa_column=Column('id', String(36, 'utf8mb4_unicode_ci'), primary_key=True))
    checksum: str = Field(sa_column=Column('checksum', String(64, 'utf8mb4_unicode_ci'), nullable=False))
    migration_name: str = Field(sa_column=Column('migration_name', String(255, 'utf8mb4_unicode_ci'), nullable=False))
    started_at: datetime.datetime = Field(sa_column=Column('started_at', DATETIME(fsp=3), nullable=False, server_default=text('CURRENT_TIMESTAMP(3)')))
    applied_steps_count: int = Field(sa_column=Column('applied_steps_count', INTEGER(unsigned=True), nullable=False, server_default=text("'0'")))
    finished_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('finished_at', DATETIME(fsp=3)))
    logs: Optional[str] = Field(default=None, sa_column=Column('logs', Text(collation='utf8mb4_unicode_ci')))
    rolled_back_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('rolled_back_at', DATETIME(fsp=3)))


# 1. THE BASE: Shared user fields
class UserBase(SQLModel):
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=100)

# 2. CREATE DTO: What the client sends when registering
class UserCreate(UserBase):
    password: str = Field(min_length=8) # Accept raw password, enforce length

# 3. LOGIN DTO: What the client sends to log in
class UserLogin(SQLModel):
    email: str
    password: str

# 4. READ DTO: What we return (NEVER include the password here)
class UserRead(UserBase):
    id: int
    created_at: Optional[datetime.datetime]

# 5. DATABASE MODEL: What is actually saved in MySQL
# 5. DATABASE MODEL: What is actually saved in MySQL
class User(UserBase, table=True):
    __table_args__ = (
        Index('email', 'email', unique=True),
    )
    
    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    email: str = Field(sa_column=Column('email', String(255), nullable=False))
    full_name: str = Field(sa_column=Column('full_name', String(100), nullable=False))
    
    hashed_password: str = Field(sa_column=Column('hashed_password', String(255), nullable=False))
    
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))
    
    # --- RESTORE THESE RELATIONSHIPS ---
    booking: list['Booking'] = Relationship(back_populates='user')
    order: list['Order'] = Relationship(back_populates='user')
    user_pass: list['UserPass'] = Relationship(back_populates='user')
    user_subscription: list['UserSubscription'] = Relationship(back_populates='user')
    booking_appointment: list['BookingAppointment'] = Relationship(back_populates='user')

class AppointmentType(SQLModel, table=True):
    __tablename__ = 'appointment_type'

    id: int = Field(sa_column=Column('id', INTEGER(unsigned=True), primary_key=True, autoincrement=True))
    name: str = Field(sa_column=Column('name', String(100), nullable=False))
    type: str = Field(sa_column=Column('type', String(50), nullable=False))
    duration_minutes: int = Field(sa_column=Column('duration_minutes', INTEGER(unsigned=True), nullable=False))
    price: decimal.Decimal = Field(sa_column=Column('price', DECIMAL(10, 2), nullable=False, server_default=text("'0.00'")))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))

    subscription: list['Subscription'] = Relationship(back_populates='appointment_type', sa_relationship_kwargs={'secondary': 'subscription_appointment_type'})
    appointment: list['Appointment'] = Relationship(back_populates='appointment_type')


class ProductType(SQLModel, table=True):
    __tablename__ = 'product_type'
    __table_args__ = (
        Index('type', 'type', unique=True),
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    type: str = Field(sa_column=Column('type', String(50), nullable=False))

    product: list['Product'] = Relationship(back_populates='product_type')


# 1. THE BASE: Shared fields for validation
class AppointmentBase(SQLModel):
    appointment_type_id: int
    begins_at: datetime.datetime
    ends_at: datetime.datetime
    price: decimal.Decimal
    spaces: int = 1

# 2. CREATE DTO: What the client sends us
class AppointmentCreate(AppointmentBase):
    pass # Inherits everything from Base, nothing more needed

# 3. READ DTO: What we send back to the client
class AppointmentRead(AppointmentBase):
    id: int
    spaces_used: int
    created_at: Optional[datetime.datetime]

# 4. DATABASE MODEL: The actual MySQL table representation
class Appointment(AppointmentBase, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['appointment_type_id'], ['appointment_type.id'], ondelete='RESTRICT', name='fk_appointment_type'),
        Index('fk_appointment_type', 'appointment_type_id')
    )
    
    # We override the base fields here to enforce your specific MySQL column types
    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    appointment_type_id: int = Field(sa_column=Column('appointment_type_id', INTEGER(unsigned=True), nullable=False))
    begins_at: datetime.datetime = Field(sa_column=Column('begins_at', TIMESTAMP, nullable=False))
    ends_at: datetime.datetime = Field(sa_column=Column('ends_at', TIMESTAMP, nullable=False))
    price: decimal.Decimal = Field(sa_column=Column('price', DECIMAL(10, 2), nullable=False, server_default=text("'0.00'")))
    spaces: int = Field(sa_column=Column('spaces', INTEGER(unsigned=True), nullable=False, server_default=text("'1'")))
    spaces_used: int = Field(sa_column=Column('spaces_used', INTEGER(unsigned=True), nullable=False, server_default=text("'0'")))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))
    
    # Relationships stay ONLY on the database model
    appointment_type: 'AppointmentType' = Relationship(back_populates='appointment')
    booking_appointment: list['BookingAppointment'] = Relationship(back_populates='appointment')

class Booking(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='RESTRICT', name='fk_booking_user'),
        Index('booking_reference', 'booking_reference', unique=True),
        Index('fk_booking_user', 'user_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    user_id: int = Field(sa_column=Column('user_id', BIGINT(unsigned=True), nullable=False))
    booking_reference: str = Field(sa_column=Column('booking_reference', String(64), nullable=False))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))
    updated_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('updated_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')))

    user: 'User' = Relationship(back_populates='booking')
    booking_appointment: list['BookingAppointment'] = Relationship(back_populates='booking')


class Order(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='RESTRICT', name='fk_user'),
        Index('fk_user', 'user_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    user_id: int = Field(sa_column=Column('user_id', BIGINT(unsigned=True), nullable=False))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))

    user: 'User' = Relationship(back_populates='order')
    order_product: list['OrderProduct'] = Relationship(back_populates='order')
    user_pass: list['UserPass'] = Relationship(back_populates='order')
    user_subscription: list['UserSubscription'] = Relationship(back_populates='order')


class Product(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['product_type_id'], ['product_type.id'], ondelete='RESTRICT', name='fk_product_type'),
        Index('fk_product_type', 'product_type_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    product_type_id: int = Field(sa_column=Column('product_type_id', BIGINT(unsigned=True), nullable=False))
    name: str = Field(sa_column=Column('name', String(150), nullable=False))
    price: decimal.Decimal = Field(sa_column=Column('price', DECIMAL(10, 2), nullable=False, server_default=text("'0.00'")))
    status: str = Field(sa_column=Column('status', String(25), nullable=False, server_default=text("'active'")))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))

    product_type: 'ProductType' = Relationship(back_populates='product')
    order_product: list['OrderProduct'] = Relationship(back_populates='product')
    pass_: list['Pass'] = Relationship(back_populates='product')
    subscription: list['Subscription'] = Relationship(back_populates='product')
    user_pass: list['UserPass'] = Relationship(back_populates='product')
    user_subscription: list['UserSubscription'] = Relationship(back_populates='product')


class OrderProduct(SQLModel, table=True):
    __tablename__ = 'order_product'
    __table_args__ = (
        ForeignKeyConstraint(['order_id'], ['order.id'], ondelete='CASCADE', name='fk_op_order'),
        ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='RESTRICT', name='fk_op_product'),
        Index('fk_op_order', 'order_id'),
        Index('fk_op_product', 'product_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    order_id: int = Field(sa_column=Column('order_id', BIGINT(unsigned=True), nullable=False))
    product_id: int = Field(sa_column=Column('product_id', BIGINT(unsigned=True), nullable=False))
    quantity: int = Field(sa_column=Column('quantity', INTEGER(unsigned=True), nullable=False, server_default=text("'1'")))
    unit_price: decimal.Decimal = Field(sa_column=Column('unit_price', DOUBLE(10, 2), nullable=False))

    order: 'Order' = Relationship(back_populates='order_product')
    product: 'Product' = Relationship(back_populates='order_product')


class Pass(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE', name='fk_pass_product'),
        Index('product_id', 'product_id', unique=True)
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    product_id: int = Field(sa_column=Column('product_id', BIGINT(unsigned=True), nullable=False))
    allowed_uses: int = Field(sa_column=Column('allowed_uses', INTEGER(unsigned=True), nullable=False, server_default=text("'1'")))
    expires_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('expires_at', TIMESTAMP))

    product: 'Product' = Relationship(back_populates='pass_')


class Subscription(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE', name='fk_subscription_product'),
        Index('fk_subscription_product', 'product_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    product_id: int = Field(sa_column=Column('product_id', BIGINT(unsigned=True), nullable=False))
    setup_fee: decimal.Decimal = Field(sa_column=Column('setup_fee', DECIMAL(10, 2), nullable=False, server_default=text("'0.00'")))
    renewel_fee: decimal.Decimal = Field(sa_column=Column('renewel_fee', DECIMAL(10, 2), nullable=False, server_default=text("'0.00'")))

    appointment_type: list['AppointmentType'] = Relationship(back_populates='subscription', sa_relationship_kwargs={'secondary': 'subscription_appointment_type'})
    product: 'Product' = Relationship(back_populates='subscription')


class UserPass(SQLModel, table=True):
    __tablename__ = 'user_pass'
    __table_args__ = (
        ForeignKeyConstraint(['order_id'], ['order.id'], ondelete='SET NULL', name='fk_up_order'),
        ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='RESTRICT', name='fk_up_product'),
        ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', name='fk_up_user'),
        Index('fk_up_order', 'order_id'),
        Index('fk_up_product', 'product_id'),
        Index('fk_up_user', 'user_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    user_id: int = Field(sa_column=Column('user_id', BIGINT(unsigned=True), nullable=False))
    product_id: int = Field(sa_column=Column('product_id', BIGINT(unsigned=True), nullable=False))
    uses_remaining: int = Field(sa_column=Column('uses_remaining', INTEGER(unsigned=True), nullable=False, server_default=text("'0'")))
    order_id: Optional[int] = Field(default=None, sa_column=Column('order_id', BIGINT(unsigned=True)))
    last_used_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('last_used_at', TIMESTAMP))
    expires_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('expires_at', TIMESTAMP))

    order: Optional['Order'] = Relationship(back_populates='user_pass')
    product: 'Product' = Relationship(back_populates='user_pass')
    user: 'User' = Relationship(back_populates='user_pass')
    booking_appointment: list['BookingAppointment'] = Relationship(back_populates='user_pass')


class UserSubscription(SQLModel, table=True):
    __tablename__ = 'user_subscription'
    __table_args__ = (
        ForeignKeyConstraint(['order_id'], ['order.id'], ondelete='SET NULL', name='fk_us_order'),
        ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='RESTRICT', name='fk_us_product'),
        ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', name='fk_us_user'),
        Index('fk_us_order', 'order_id'),
        Index('fk_us_product', 'product_id'),
        Index('fk_us_user', 'user_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    product_id: int = Field(sa_column=Column('product_id', BIGINT(unsigned=True), nullable=False))
    user_id: int = Field(sa_column=Column('user_id', BIGINT(unsigned=True), nullable=False))
    expires_at: datetime.datetime = Field(sa_column=Column('expires_at', TIMESTAMP, nullable=False))
    order_id: Optional[int] = Field(default=None, sa_column=Column('order_id', BIGINT(unsigned=True)))
    last_used_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('last_used_at', TIMESTAMP))

    order: Optional['Order'] = Relationship(back_populates='user_subscription')
    product: 'Product' = Relationship(back_populates='user_subscription')
    user: 'User' = Relationship(back_populates='user_subscription')
    booking_appointment: list['BookingAppointment'] = Relationship(back_populates='user_subscription')


class BookingAppointment(SQLModel, table=True):
    __tablename__ = 'booking_appointment'
    __table_args__ = (
        ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ondelete='RESTRICT', name='fk_ba_appointment'),
        ForeignKeyConstraint(['booking_id'], ['booking.id'], ondelete='CASCADE', name='fk_ba_booking'),
        ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='RESTRICT', name='fk_ba_user'),
        ForeignKeyConstraint(['user_pass_id'], ['user_pass.id'], ondelete='SET NULL', name='fk_ba_pass'),
        ForeignKeyConstraint(['user_subscription_id'], ['user_subscription.id'], ondelete='SET NULL', name='fk_ba_sub'),
        Index('fk_ba_appointment', 'appointment_id'),
        Index('fk_ba_booking', 'booking_id'),
        Index('fk_ba_pass', 'user_pass_id'),
        Index('fk_ba_sub', 'user_subscription_id'),
        Index('fk_ba_user', 'user_id')
    )

    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    booking_id: int = Field(sa_column=Column('booking_id', BIGINT(unsigned=True), nullable=False))
    appointment_id: int = Field(sa_column=Column('appointment_id', BIGINT(unsigned=True), nullable=False))
    user_id: int = Field(sa_column=Column('user_id', BIGINT(unsigned=True), nullable=False))
    has_paid: int = Field(sa_column=Column('has_paid', TINYINT(1), nullable=False, server_default=text("'0'")))
    user_pass_id: Optional[int] = Field(default=None, sa_column=Column('user_pass_id', BIGINT(unsigned=True)))
    user_subscription_id: Optional[int] = Field(default=None, sa_column=Column('user_subscription_id', BIGINT(unsigned=True)))

    appointment: 'Appointment' = Relationship(back_populates='booking_appointment')
    booking: 'Booking' = Relationship(back_populates='booking_appointment')
    user: 'User' = Relationship(back_populates='booking_appointment')
    user_pass: Optional['UserPass'] = Relationship(back_populates='booking_appointment')
    user_subscription: Optional['UserSubscription'] = Relationship(back_populates='booking_appointment')


t_subscription_appointment_type = Table(
    'subscription_appointment_type', SQLModel.metadata,
    Column('subscription_id', BIGINT(unsigned=True), primary_key=True),
    Column('appointment_type_id', INTEGER(unsigned=True), primary_key=True),
    ForeignKeyConstraint(['appointment_type_id'], ['appointment_type.id'], ondelete='CASCADE', name='fk_sat_appointment_type'),
    ForeignKeyConstraint(['subscription_id'], ['subscription.id'], ondelete='CASCADE', name='fk_sat_subscription'),
    Index('fk_sat_appointment_type', 'appointment_type_id')
)
