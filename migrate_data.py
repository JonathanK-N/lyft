"""
Script de migration des données de l'ancienne structure vers la nouvelle
"""
import sqlite3
import os
from app import create_app, db
from app.models.user import Member

def migrate_data():
    """Migrer les données de l'ancienne base vers la nouvelle structure"""
    old_db_path = "church_lyft.db"
    
    if not os.path.exists(old_db_path):
        print("Aucune ancienne base de données trouvée.")
        return
    
    app = create_app()
    
    with app.app_context():
        # Connexion à l'ancienne base
        old_conn = sqlite3.connect(old_db_path)
        old_cursor = old_conn.cursor()
        
        try:
            # Récupérer toutes les données de l'ancienne table
            old_cursor.execute("SELECT * FROM member")
            old_members = old_cursor.fetchall()
            
            # Obtenir les noms des colonnes
            old_cursor.execute("PRAGMA table_info(member)")
            columns = [column[1] for column in old_cursor.fetchall()]
            
            print(f"Migration de {len(old_members)} membres...")
            
            for row in old_members:
                member_data = dict(zip(columns, row))
                
                # Créer le nouveau membre
                new_member = Member(
                    name=member_data.get('name'),
                    address=member_data.get('address'),
                    lat=member_data.get('lat'),
                    lon=member_data.get('lon'),
                    has_vehicle=bool(member_data.get('has_vehicle', 0)),
                    can_drive=bool(member_data.get('can_drive', 0)),
                    capacity=member_data.get('capacity', 0),
                    wants_ride=bool(member_data.get('wants_ride', 0))
                )
                
                db.session.add(new_member)
            
            db.session.commit()
            print("✅ Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()
        finally:
            old_conn.close()

if __name__ == "__main__":
    migrate_data()