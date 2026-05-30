"""
内容商店API路由
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.recommendation_service import RecommendationEngine
from models.content_store import (
    ContentCategory,
    ContentItem,
    ContentRating,
    ContentReview,
    ContentStatus,
    ContentType,
    Order,
    OrderItem,
    OrderStatus,
    ShoppingCartItem,
)
from models.subscription import SubscriptionStatus, UserSubscription
from models.user import User
from routes.auth_routes import get_current_user
from services.drm_service import get_drm_service
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/store", tags=["内容商店"])


# 内容浏览和搜索API
@router.get("/contents", response_model=List[Dict[str, Any]])
async def get_contents(
    category_id: Optional[str] = Query(None, description="分类ID"),
    content_type: Optional[ContentType] = Query(None, description="内容类型"),
    rating: Optional[ContentRating] = Query(None, description="评级要求"),
    is_free: Optional[bool] = Query(None, description="是否免费"),
    is_featured: Optional[bool] = Query(None, description="是否推荐"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query(
        "popular", description="排序方式: popular, newest, price_low, price_high"
    ),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取内容列表
    """
    try:
        from sqlalchemy import asc, desc, or_, select

        # 构建查询
        query = select(ContentItem).where(ContentItem.status == ContentStatus.PUBLISHED)

        # 添加筛选条件
        if category_id:
            query = query.where(ContentItem.category_id == category_id)

        if content_type:
            query = query.where(ContentItem.content_type == content_type)

        if rating:
            query = query.where(ContentItem.rating == rating)

        if is_free is not None:
            query = query.where(ContentItem.is_free == is_free)

        if is_featured is not None:
            query = query.where(ContentItem.is_featured == is_featured)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    ContentItem.title.like(search_term),
                    ContentItem.description.like(search_term),
                )
            )

        # 添加排序
        if sort_by == "popular":
            query = query.order_by(
                desc(ContentItem.purchase_count), desc(ContentItem.view_count)
            )
        elif sort_by == "newest":
            query = query.order_by(desc(ContentItem.published_at))
        elif sort_by == "price_low":
            query = query.order_by(asc(ContentItem.price))
        elif sort_by == "price_high":
            query = query.order_by(desc(ContentItem.price))

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        contents = result.scalars().all()

        # 转换为响应格式
        response_data = []
        for content in contents:
            content_dict = {
                "content_id": content.content_id,
                "title": content.title,
                "description": content.description,
                "content_type": content.content_type.value,
                "rating_required": content.rating.value,
                "price": content.price,
                "original_price": content.original_price,
                "is_free": content.is_free,
                "thumbnail_url": content.thumbnail_url,
                "preview_url": content.preview_url,
                "view_count": content.view_count,
                "purchase_count": content.purchase_count,
                "rating_score": content.rating_score,
                "rating_count": content.rating_count,
                "is_featured": content.is_featured,
                "published_at": (
                    content.published_at.isoformat() if content.published_at else None
                ),
                "has_drm": content.has_drm,
            }
            response_data.append(content_dict)

        return response_data

    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取内容列表失败")


@router.get("/contents/{content_id}", response_model=Dict[str, Any])
async def get_content_detail(
    content_id: str = Path(..., description="内容ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取内容详情
    """
    try:
        from sqlalchemy import select

        # 查询内容详情
        content_query = select(ContentItem).where(
            ContentItem.content_id == content_id,
            ContentItem.status == ContentStatus.PUBLISHED,
        )
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        # 增加查看次数
        content.view_count += 1
        await db.commit()

        # 获取用户对该内容的访问权限
        has_access = await _check_user_access(current_user.id, content_id, db)

        # 获取用户评分
        user_rating = await _get_user_rating(current_user.id, content_id, db)

        # 获取相关推荐
        recommendation_engine = RecommendationEngine()
        related_recommendations = await recommendation_engine.get_recommendations(
            current_user.id, db, num_recommendations=5
        )

        response_data = {
            "content_id": content.content_id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type.value,
            "rating_required": content.rating.value,
            "price": content.price,
            "original_price": content.original_price,
            "is_free": content.is_free,
            "currency": content.currency,
            "thumbnail_url": content.thumbnail_url,
            "preview_url": content.preview_url,
            "demo_url": content.demo_url,
            "view_count": content.view_count,
            "download_count": content.download_count,
            "purchase_count": content.purchase_count,
            "rating_score": content.rating_score,
            "rating_count": content.rating_count,
            "seo_keywords": content.seo_keywords,
            "meta_description": content.meta_description,
            "is_featured": content.is_featured,
            "published_at": (
                content.published_at.isoformat() if content.published_at else None
            ),
            "has_drm": content.has_drm,
            "has_access": has_access,
            "user_rating": user_rating,
            "related_recommendations": related_recommendations,
            "version": content.version,
            "file_size": content.file_size,
            "file_format": content.file_format,
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取内容详情失败")


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories(
    include_empty: bool = Query(False, description="是否包含空分类"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取内容分类列表
    """
    try:
        from sqlalchemy import func, select

        query = select(ContentCategory)

        if not include_empty:
            # 只返回有内容的分类
            content_count_query = (
                select(
                    ContentCategory.category_id,
                    func.count(ContentItem.id).label("content_count"),
                )
                .outerjoin(
                    ContentItem, ContentItem.category_id == ContentCategory.category_id
                )
                .group_by(ContentCategory.category_id)
                .subquery()
            )

            query = query.join(
                content_count_query,
                ContentCategory.category_id == content_count_query.c.category_id,
            ).where(content_count_query.c.content_count > 0)

        query = query.where(ContentCategory.is_active == True)
        query = query.order_by(ContentCategory.sort_order, ContentCategory.name)

        result = await db.execute(query)
        categories = result.scalars().all()

        response_data = []
        for category in categories:
            category_dict = {
                "category_id": category.category_id,
                "name": category.name,
                "description": category.description,
                "icon": category.icon,
                "sort_order": category.sort_order,
            }
            response_data.append(category_dict)

        return response_data

    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取分类列表失败")


@router.get("/search", response_model=Dict[str, Any])
async def search_contents(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category_id: Optional[str] = Query(None, description="分类ID"),
    content_type: Optional[ContentType] = Query(None, description="内容类型"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索内容
    """
    try:
        from sqlalchemy import desc, func, or_, select

        # 构建搜索查询
        query = select(ContentItem).where(ContentItem.status == ContentStatus.PUBLISHED)

        # 搜索条件
        search_terms = q.split()
        search_conditions = []

        for term in search_terms:
            term_pattern = f"%{term}%"
            search_conditions.append(
                or_(
                    ContentItem.title.like(term_pattern),
                    ContentItem.description.like(term_pattern),
                    ContentItem.meta_description.like(term_pattern),
                )
            )

        # 应用所有搜索条件
        for condition in search_conditions:
            query = query.where(condition)

        # 添加其他筛选条件
        if category_id:
            query = query.where(ContentItem.category_id == category_id)

        if content_type:
            query = query.where(ContentItem.content_type == content_type)

        # 计算总数量
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()

        # 添加排序和分页
        query = query.order_by(
            desc(func.similarity(ContentItem.title, q)),  # 标题相关性
            desc(ContentItem.purchase_count),  # 购买数量
            desc(ContentItem.rating_score),  # 评分
        )

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        contents = result.scalars().all()

        # 转换结果
        items = []
        for content in contents:
            items.append(
                {
                    "content_id": content.content_id,
                    "title": content.title,
                    "description": content.description,
                    "content_type": content.content_type.value,
                    "price": content.price,
                    "is_free": content.is_free,
                    "thumbnail_url": content.thumbnail_url,
                    "rating_score": content.rating_score,
                    "purchase_count": content.purchase_count,
                }
            )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"内容搜索失败: {e}")
        raise HTTPException(status_code=500, detail="搜索失败")


# 购物车API
@router.post("/cart/items", response_model=Dict[str, Any])
async def add_to_cart(
    content_id: str = Body(..., description="内容ID"),
    quantity: int = Body(1, ge=1, description="数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    添加商品到购物车
    """
    try:
        import uuid

        from sqlalchemy import select

        # 检查内容是否存在
        content_query = select(ContentItem).where(
            ContentItem.content_id == content_id,
            ContentItem.status == ContentStatus.PUBLISHED,
        )
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="内容不存在")

        # 检查用户是否已经有该商品在购物车
        existing_query = select(ShoppingCartItem).where(
            ShoppingCartItem.user_id == current_user.id,
            ShoppingCartItem.content_id == content_id,
        )
        existing_result = await db.execute(existing_query)
        existing_item = existing_result.scalar_one_or_none()

        if existing_item:
            # 更新数量
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.utcnow()
            cart_item_id = existing_item.cart_item_id
        else:
            # 创建新购物车项
            cart_item = ShoppingCartItem(
                cart_item_id=f"CART{uuid.uuid4().hex[:16].upper()}",
                user_id=current_user.id,
                content_id=content_id,
                quantity=quantity,
            )
            db.add(cart_item)
            await db.commit()
            await db.refresh(cart_item)
            cart_item_id = cart_item.cart_item_id

        return {
            "cart_item_id": cart_item_id,
            "content_id": content_id,
            "quantity": existing_item.quantity if existing_item else quantity,
            "message": "商品已添加到购物车",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加到购物车失败: {e}")
        raise HTTPException(status_code=500, detail="添加到购物车失败")


@router.get("/cart", response_model=Dict[str, Any])
async def get_cart(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    获取用户购物车
    """
    try:
        from sqlalchemy import select

        # 查询购物车项目
        cart_query = (
            select(ShoppingCartItem)
            .where(ShoppingCartItem.user_id == current_user.id)
            .order_by(ShoppingCartItem.added_at.desc())
        )

        cart_result = await db.execute(cart_query)
        cart_items = cart_result.scalars().all()

        # 计算总计
        total_amount = 0
        items_data = []

        for item in cart_items:
            # 获取内容信息
            content_query = select(ContentItem).where(
                ContentItem.content_id == item.content_id
            )
            content_result = await db.execute(content_query)
            content = content_result.scalar_one_or_none()

            if content:
                item_total = content.price * item.quantity
                total_amount += item_total

                items_data.append(
                    {
                        "cart_item_id": item.cart_item_id,
                        "content_id": item.content_id,
                        "title": content.title,
                        "price": content.price,
                        "quantity": item.quantity,
                        "subtotal": item_total,
                        "thumbnail_url": content.thumbnail_url,
                        "content_type": content.content_type.value,
                    }
                )

        return {
            "items": items_data,
            "item_count": len(items_data),
            "total_amount": round(total_amount, 2),
        }

    except Exception as e:
        logger.error(f"获取购物车失败: {e}")
        raise HTTPException(status_code=500, detail="获取购物车失败")


@router.delete("/cart/items/{cart_item_id}")
async def remove_from_cart(
    cart_item_id: str = Path(..., description="购物车项ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    从购物车移除商品
    """
    try:
        from sqlalchemy import delete, select

        # 验证购物车项所有权
        cart_item_query = select(ShoppingCartItem).where(
            ShoppingCartItem.cart_item_id == cart_item_id,
            ShoppingCartItem.user_id == current_user.id,
        )
        cart_item_result = await db.execute(cart_item_query)
        cart_item = cart_item_result.scalar_one_or_none()

        if not cart_item:
            raise HTTPException(status_code=404, detail="购物车项不存在")

        # 删除购物车项
        delete_query = delete(ShoppingCartItem).where(
            ShoppingCartItem.cart_item_id == cart_item_id
        )
        await db.execute(delete_query)
        await db.commit()

        return {"message": "商品已从购物车移除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除购物车商品失败: {e}")
        raise HTTPException(status_code=500, detail="移除购物车商品失败")


# 订单API
@router.post("/orders", response_model=Dict[str, Any])
async def create_order(
    cart_item_ids: List[str] = Body(..., description="购物车项ID列表"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建订单
    """
    try:
        import uuid

        from sqlalchemy import select

        # 验证购物车项
        cart_items = []
        total_amount = 0

        for cart_item_id in cart_item_ids:
            cart_item_query = select(ShoppingCartItem).where(
                ShoppingCartItem.cart_item_id == cart_item_id,
                ShoppingCartItem.user_id == current_user.id,
            )
            cart_item_result = await db.execute(cart_item_query)
            cart_item = cart_item_result.scalar_one_or_none()

            if not cart_item:
                raise HTTPException(
                    status_code=404, detail=f"购物车项 {cart_item_id} 不存在"
                )

            # 获取内容价格
            content_query = select(ContentItem).where(
                ContentItem.content_id == cart_item.content_id
            )
            content_result = await db.execute(content_query)
            content = content_result.scalar_one_or_none()

            if not content:
                raise HTTPException(
                    status_code=404, detail=f"内容 {cart_item.content_id} 不存在"
                )

            cart_items.append(
                {
                    "cart_item": cart_item,
                    "content": content,
                    "subtotal": content.price * cart_item.quantity,
                }
            )
            total_amount += content.price * cart_item.quantity

        # 创建订单
        order = Order(
            order_id=f"ORDER{uuid.uuid4().hex[:16].upper()}",
            user_id=current_user.id,
            status=OrderStatus.PENDING,
            subtotal=round(total_amount, 2),
            total_amount=round(total_amount, 2),
            currency="CNY",
        )

        db.add(order)
        await db.flush()  # 获取order_id

        # 创建订单项
        for item_data in cart_items:
            cart_item = item_data["cart_item"]
            content = item_data["content"]

            order_item = OrderItem(
                order_item_id=f"ITEM{uuid.uuid4().hex[:16].upper()}",
                order_id=order.order_id,
                content_id=content.content_id,
                unit_price=content.price,
                quantity=cart_item.quantity,
                subtotal=item_data["subtotal"],
                content_title=content.title,
                content_version=content.version,
            )

            db.add(order_item)

        # 删除购物车项
        for item_data in cart_items:
            await db.delete(item_data["cart_item"])

        await db.commit()
        await db.refresh(order)

        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "message": "订单创建成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        raise HTTPException(status_code=500, detail="创建订单失败")


@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def get_order_detail(
    order_id: str = Path(..., description="订单ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订单详情
    """
    try:
        from sqlalchemy import select

        # 验证订单所有权
        order_query = select(Order).where(
            Order.order_id == order_id, Order.user_id == current_user.id
        )
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 获取订单项
        items_query = select(OrderItem).where(OrderItem.order_id == order_id)
        items_result = await db.execute(items_query)
        order_items = items_result.scalars().all()

        items_data = []
        for item in order_items:
            items_data.append(
                {
                    "order_item_id": item.order_item_id,
                    "content_id": item.content_id,
                    "content_title": item.content_title,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "subtotal": item.subtotal,
                }
            )

        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "subtotal": order.subtotal,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "created_at": order.created_at.isoformat(),
            "items": items_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取订单详情失败")


# DRM内容访问API
@router.get("/content/{content_id}/access-token", response_model=Dict[str, Any])
async def get_content_access_token(
    content_id: str = Path(..., description="内容ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取内容访问令牌
    """
    try:
        # 检查访问权限
        has_access = await _check_user_access(current_user.id, content_id, db)
        if not has_access:
            raise HTTPException(status_code=403, detail="无访问权限")

        # 生成访问令牌
        drm_service = get_drm_service()
        access_token = drm_service._generate_access_token(current_user.id, content_id)

        return {
            "access_token": access_token,
            "content_id": content_id,
            "user_id": current_user.id,
            "expires_in": 3600,  # 1小时过期
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成访问令牌失败: {e}")
        raise HTTPException(status_code=500, detail="生成访问令牌失败")


@router.get("/content/{content_id}/stream")
async def stream_content(
    content_id: str = Path(..., description="内容ID"),
    access_token: str = Query(..., description="访问令牌"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    流式传输加密内容
    """
    try:
        # 验证访问令牌
        drm_service = get_drm_service()
        # 这里应该验证令牌有效性

        # 解密并流式传输内容
        device_info = {
            "userAgent": "web-browser",
            "ipAddress": "127.0.0.1",  # 实际应用中从请求头获取
        }

        decrypted_content = await drm_service.decrypt_content(
            content_id, current_user.id, device_info, db
        )

        if not decrypted_content:
            raise HTTPException(status_code=403, detail="无法访问内容")

        # 返回内容流（简化实现）
        return {
            "content": decrypted_content.decode("utf-8", errors="ignore")[:1000]
            + "...",
            "content_type": "application/octet-stream",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"内容流传输失败: {e}")
        raise HTTPException(status_code=500, detail="内容传输失败")


# 辅助函数
async def _check_user_access(user_id: str, content_id: str, db: AsyncSession) -> bool:
    """检查用户对内容的访问权限"""
    try:
        from sqlalchemy import select

        # 检查是否已购买
        order_query = (
            select(Order)
            .join(OrderItem)
            .where(
                Order.user_id == user_id,
                OrderItem.content_id == content_id,
                Order.status == OrderStatus.COMPLETED,
            )
        )
        order_result = await db.execute(order_query)
        if order_result.scalar_one_or_none():
            return True

        # 检查订阅权限
        subscription_query = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status.in_(
                [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            ),
        )
        subscription_result = await db.execute(subscription_query)
        subscriptions = subscription_result.scalars().all()

        # 获取内容评级要求
        content_query = select(ContentItem).where(ContentItem.content_id == content_id)
        content_result = await db.execute(content_query)
        content = content_result.scalar_one_or_none()

        if content and subscriptions:
            content.rating
            # 这里应该检查用户的订阅等级是否满足内容要求
            return True  # 简化实现

        # 检查是否为免费内容
        if content and content.is_free:
            return True

        return False

    except Exception as e:
        logger.error(f"检查访问权限失败: {e}")
        return False


async def _get_user_rating(
    user_id: str, content_id: str, db: AsyncSession
) -> Optional[float]:
    """获取用户对内容的评分"""
    try:
        from sqlalchemy import select

        review_query = select(ContentReview).where(
            ContentReview.user_id == user_id, ContentReview.content_id == content_id
        )
        review_result = await db.execute(review_query)
        review = review_result.scalar_one_or_none()

        return review.rating if review else None

    except Exception as e:
        logger.error(f"获取用户评分失败: {e}")
        return None
