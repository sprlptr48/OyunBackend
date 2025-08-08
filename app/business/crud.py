from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from .models import Branch, Business  # Assuming models are in the same directory/module
from .schemas import BranchUpdateSchema


def business_near_point(point: Point, radius: int, db: Session):
    """
    Finds active branches within a given radius of a point.
    Optimized to pre-load business data to avoid N+1 queries.
    """
    search_point_wkb = from_shape(point, srid=4326)

    query = db.query(Branch).options(
        # --- OPTIMIZATION ---
        # Eagerly loads the related Business object in the same query.
        # This prevents a separate DB call for each branch to get its name.
        joinedload(Branch.business)
    ).filter(
        # --- FILTER ---
        # Ensures only active and available branches are returned.
        Branch.is_active == True,

        # Geospatial filter to find branches within the specified radius.
        ST_DWithin(
            Branch.location,
            search_point_wkb,
            radius
        )
    )

    return query.all()


def find_nearest_businesses_ordered(lat: float, lon: float, limit: int, db: Session):
    """
    Finds a limited number of the nearest active branches to a point,
    ordered by distance. Optimized to pre-load business data.
    """
    user_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    query = db.query(
        Branch,
        ST_Distance(Branch.location, user_point).label('distance')
    ).options(
        joinedload(Branch.business)
    ).filter(
        Branch.is_active == True # Only open branches
    ).order_by(
        'distance'  # Order by the calculated distance, closest first
    ).limit(
        limit
    )

    return query.all()

def get_branch_with_details_by_id(db: Session, branch_id: int):
    """
    Verilen ID'ye sahip aktif bir şubeyi, bağlı olduğu aktif işletme
    bilgileriyle birlikte getirir.
    """
    return db.query(Branch).options(
        joinedload(Branch.business)
    ).filter(
        Branch.id == branch_id,
        Branch.is_active == True,
        Branch.business.has(Business.is_active == True)
    ).first()


def get_branch_by_id(db: Session, branch_id: int) -> Branch | None:
    """
    Tek bir şubeyi ID'sine göre getirir.
    Performans için ilişkili 'business' verisini de aynı sorguda yükler (joinedload).
    """
    return db.query(Branch).options(
        joinedload(Branch.business)
    ).filter(Branch.id == branch_id).first()


def update_branch(db: Session, db_branch: Branch, update_data: BranchUpdateSchema) -> Branch:
    """
    Mevcut bir Branch nesnesini yeni verilerle günceller ve veritabanına kaydeder.
    """
    update_dict = update_data.model_dump(exclude_unset=True) #sadece gönderilen verileri ekle

    for key, value in update_dict.items():
        # Konum verisi özel işlem gerektirir.
        if key == "location" and value is not None:
            point = Point(value['longitude'], value['latitude'])
            setattr(db_branch, key, from_shape(point, srid=4326))
        else:
            setattr(db_branch, key, value)

    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch


def get_business_with_branches_by_id(db: Session, business_id: int) -> Business | None:
    """
    Verilen ID'ye sahip işletmeyi, ilişkili tüm şubeleriyle birlikte getirir.
    Performans için `selectinload` kullanılarak N+1 sorgu problemi önlenir.
    """
    query = db.query(Business).options(
        selectinload(Business.branches)
    ).filter(Business.id == business_id)

    return query.first()


def search_branches(db: Session, keyword: str, point: Optional[Point] = None, radius: Optional[int] = None)\
        -> list[Branch]:
    """
    Anahtar kelimeye ve opsiyonel olarak lokasyona göre şubeleri arar.
    - `business.name` ve `branch.address_text` alanlarında arama yapar.
    - Sadece aktif şubeleri ve işletmeleri döndürür.
    - Performans için 'business' verisini önceden yükler.
    """
    # Temel sorgu: Branch ve Business tablolarını birleştirir.
    query = db.query(Branch).join(Branch.business).options(
        joinedload(Branch.business)
    )
    # Filtre 1: Anahtar Kelime (Case-insensitive)
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                Business.name.ilike(search_term),
                Branch.address_text.ilike(search_term)
            )
        )
    # Filtre 2: Lokasyon (Eğer parametreler verildiyse)
    if point and radius:
        search_point_wkb = from_shape(point, srid=4326)
        query = query.filter(
            ST_DWithin(Branch.location, search_point_wkb, radius)
        )
    # Filtre 3: Sadece Aktif Olanlar
    # Hem şubenin hem de ana işletmenin aktif olması önemlidir.
    query = query.filter(
        Branch.is_active == True,
        Business.is_active == True
    )

    return query.all()

def delete_branch(db: Session, db_branch: Branch) -> None:
    """
    Verilen Branch nesnesini veritabanından siler.
    """
    db.delete(db_branch)
    db.commit()
    return
