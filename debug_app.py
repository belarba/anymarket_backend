#!/usr/bin/env python3
"""
Script de debug completo para diagnosticar problemas
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("=" * 60)
    print("🔧 DEBUG COMPLETO - ANYMARKET BACKEND")
    print("=" * 60)
    
    # 1. Verificar ambiente
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    print(f"🔗 DATABASE_URL: {database_url[:50]}...")
    
    # 2. Testar importações
    print("\n📦 TESTANDO IMPORTAÇÕES:")
    try:
        from app.database import engine, test_connection, SessionLocal
        print("   ✅ app.database importado")
        
        from app import models
        print("   ✅ app.models importado")
        
        from sqlalchemy import inspect, text
        print("   ✅ sqlalchemy importado")
        
    except Exception as e:
        print(f"   ❌ Erro nas importações: {e}")
        return
    
    # 3. Testar conexão
    print("\n🔍 TESTANDO CONEXÃO:")
    if test_connection():
        print("   ✅ Conexão OK")
    else:
        print("   ❌ Falha na conexão")
        return
    
    # 4. Verificar tabelas existentes
    print("\n📋 VERIFICANDO TABELAS EXISTENTES:")
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            print(f"   ✅ {len(existing_tables)} tabelas encontradas:")
            for table in existing_tables:
                print(f"      - {table}")
        else:
            print("   ❌ Nenhuma tabela encontrada")
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar tabelas: {e}")
    
    # 5. Tentar criar tabelas manualmente
    print("\n🔨 CRIANDO TABELAS MANUALMENTE:")
    try:
        print("   📋 Criando tabela 'products'...")
        models.Base.metadata.create_all(bind=engine)
        print("   ✅ Comando create_all executado")
        
        # Verificar novamente
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        
        if new_tables:
            print(f"   ✅ {len(new_tables)} tabelas após criação:")
            for table in new_tables:
                print(f"      - {table}")
        else:
            print("   ❌ Ainda nenhuma tabela encontrada")
            
    except Exception as e:
        print(f"   ❌ Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Testar inserção manual
    print("\n🧪 TESTE DE INSERÇÃO MANUAL:")
    try:
        db = SessionLocal()
        
        # Tentar criar um produto de teste
        test_product = models.Product(
            anymarket_id="test_123",
            title="Produto Teste",
            description="Descrição teste",
            price=99.99,
            brand="Marca Teste",
            sku="TEST123"
        )
        
        db.add(test_product)
        db.commit()
        
        # Verificar se foi salvo
        saved_product = db.query(models.Product).filter(
            models.Product.anymarket_id == "test_123"
        ).first()
        
        if saved_product:
            print("   ✅ Produto de teste salvo com sucesso")
            print(f"      ID: {saved_product.id}")
            print(f"      Título: {saved_product.title}")
            
            # Limpar teste
            db.delete(saved_product)
            db.commit()
            print("   🧹 Produto de teste removido")
        else:
            print("   ❌ Produto de teste não foi salvo")
            
        db.close()
        
    except Exception as e:
        print(f"   ❌ Erro no teste de inserção: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Verificar estrutura das tabelas
    print("\n🏗️  ESTRUTURA DAS TABELAS:")
    try:
        with engine.connect() as conn:
            # Verificar tabela products
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'products'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                print("   📋 Estrutura da tabela 'products':")
                for col in columns:
                    print(f"      - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("   ❌ Tabela 'products' não encontrada na estrutura")
            
            # Verificar tabela orders
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'orders'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                print("   📋 Estrutura da tabela 'orders':")
                for col in columns:
                    print(f"      - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("   ❌ Tabela 'orders' não encontrada na estrutura")
                
    except Exception as e:
        print(f"   ❌ Erro ao verificar estrutura: {e}")
    
    print("\n" + "=" * 60)
    print("✅ DEBUG CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    main()