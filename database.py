"""
Database models and operations for DNA Art Generator
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DNASequence(Base):
    """Store DNA sequence information and analysis results"""
    __tablename__ = "dna_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    organism_name = Column(String(255), nullable=False, index=True)
    ncbi_id = Column(String(100), nullable=False, unique=True)
    sequence_length = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    gc_content = Column(Float, nullable=False)
    adenine_count = Column(Integer, nullable=False)
    thymine_count = Column(Integer, nullable=False)
    cytosine_count = Column(Integer, nullable=False)
    guanine_count = Column(Integer, nullable=False)
    unknown_count = Column(Integer, nullable=False, default=0)
    sequence_sample = Column(Text, nullable=True)  # First 200 bases for preview
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_count = Column(Integer, default=1)
    last_accessed = Column(DateTime, default=datetime.utcnow)

class SearchHistory(Base):
    """Track user search history and popular organisms"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    organism_name = Column(String(255), nullable=False, index=True)
    search_successful = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    user_session = Column(String(100), nullable=True)  # For session tracking

class UserFavorites(Base):
    """Store user favorite organisms (session-based)"""
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_session = Column(String(100), nullable=False, index=True)
    organism_name = Column(String(255), nullable=False)
    ncbi_id = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_dna_sequence(organism_name, seq_record, gc_content, base_counts):
    """Save DNA sequence analysis to database"""
    db = SessionLocal()
    try:
        # Check if sequence already exists
        existing = db.query(DNASequence).filter(DNASequence.ncbi_id == seq_record.id).first()
        
        if existing:
            # Update access statistics
            existing.accessed_count += 1
            existing.last_accessed = datetime.utcnow()
            db.commit()
            logger.info(f"Updated access count for {seq_record.id}")
            return existing
        
        # Create new sequence record
        sequence_sample = str(seq_record.seq)[:200] if len(str(seq_record.seq)) > 200 else str(seq_record.seq)
        
        dna_seq = DNASequence(
            organism_name=organism_name,
            ncbi_id=seq_record.id,
            sequence_length=len(seq_record.seq),
            description=seq_record.description,
            gc_content=gc_content,
            adenine_count=base_counts.get('A', 0),
            thymine_count=base_counts.get('T', 0),
            cytosine_count=base_counts.get('C', 0),
            guanine_count=base_counts.get('G', 0),
            unknown_count=base_counts.get('N', 0),
            sequence_sample=sequence_sample
        )
        
        db.add(dna_seq)
        db.commit()
        db.refresh(dna_seq)
        logger.info(f"Saved new DNA sequence: {seq_record.id}")
        return dna_seq
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error saving DNA sequence: {e}")
        return None
    finally:
        db.close()

def log_search(organism_name, successful=True, error_message=None, user_session=None):
    """Log search attempt to database"""
    db = SessionLocal()
    try:
        search_log = SearchHistory(
            organism_name=organism_name,
            search_successful=successful,
            error_message=error_message,
            user_session=user_session
        )
        
        db.add(search_log)
        db.commit()
        logger.info(f"Logged search for: {organism_name}")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error logging search: {e}")
    finally:
        db.close()

def get_popular_organisms(limit=10):
    """Get most popular searched organisms"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        popular = db.query(
            SearchHistory.organism_name,
            func.count(SearchHistory.organism_name).label('search_count')
        ).filter(
            SearchHistory.search_successful == True
        ).group_by(
            SearchHistory.organism_name
        ).order_by(
            func.count(SearchHistory.organism_name).desc()
        ).limit(limit).all()
        
        return [{'organism': org, 'count': count} for org, count in popular]
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting popular organisms: {e}")
        return []
    finally:
        db.close()

def get_recent_sequences(limit=5):
    """Get recently accessed DNA sequences"""
    db = SessionLocal()
    try:
        recent = db.query(DNASequence).order_by(
            DNASequence.last_accessed.desc()
        ).limit(limit).all()
        
        return recent
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting recent sequences: {e}")
        return []
    finally:
        db.close()

def add_favorite(user_session, organism_name, ncbi_id):
    """Add organism to user favorites"""
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(UserFavorites).filter(
            UserFavorites.user_session == user_session,
            UserFavorites.ncbi_id == ncbi_id
        ).first()
        
        if existing:
            return False  # Already in favorites
        
        favorite = UserFavorites(
            user_session=user_session,
            organism_name=organism_name,
            ncbi_id=ncbi_id
        )
        
        db.add(favorite)
        db.commit()
        logger.info(f"Added favorite: {organism_name} for session {user_session}")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error adding favorite: {e}")
        return False
    finally:
        db.close()

def get_user_favorites(user_session):
    """Get user's favorite organisms"""
    db = SessionLocal()
    try:
        favorites = db.query(UserFavorites).filter(
            UserFavorites.user_session == user_session
        ).order_by(UserFavorites.added_at.desc()).all()
        
        return favorites
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting user favorites: {e}")
        return []
    finally:
        db.close()

def get_database_stats():
    """Get database statistics for admin dashboard"""
    db = SessionLocal()
    try:
        total_sequences = db.query(DNASequence).count()
        total_searches = db.query(SearchHistory).count()
        successful_searches = db.query(SearchHistory).filter(SearchHistory.search_successful == True).count()
        total_favorites = db.query(UserFavorites).count()
        
        return {
            'total_sequences': total_sequences,
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'success_rate': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
            'total_favorites': total_favorites
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting database stats: {e}")
        return {}
    finally:
        db.close()

# Initialize database on import
if __name__ == "__main__":
    create_tables()