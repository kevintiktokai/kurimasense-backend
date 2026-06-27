-- Migration 003: Financial / Exposure Layer (Sprint 2)
-- grower_contracts, input_disbursements, deliveries
-- Idempotent: running twice is a clean no-op.

CREATE TABLE IF NOT EXISTS grower_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    grower_id UUID REFERENCES growers(id),
    season_year INTEGER NOT NULL,
    crop_type TEXT,
    contracted_volume_tonnes DECIMAL(12,2),
    contract_price_per_tonne DECIMAL(12,2),
    input_credit_value DECIMAL(14,2),
    status TEXT DEFAULT 'active'
        CHECK (status IN ('active','completed','defaulted','cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contracts_tenant_season ON grower_contracts(tenant_id, season_year);
CREATE INDEX IF NOT EXISTS idx_contracts_grower ON grower_contracts(grower_id);

CREATE TABLE IF NOT EXISTS input_disbursements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    grower_id UUID REFERENCES growers(id),
    contract_id UUID REFERENCES grower_contracts(id) ON DELETE CASCADE,
    disbursement_date DATE DEFAULT CURRENT_DATE,
    input_type TEXT,
    quantity DECIMAL(12,2),
    unit TEXT,
    credit_value DECIMAL(14,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_disbursements_grower ON input_disbursements(grower_id);
CREATE INDEX IF NOT EXISTS idx_disbursements_contract ON input_disbursements(contract_id);
CREATE INDEX IF NOT EXISTS idx_disbursements_tenant ON input_disbursements(tenant_id);

CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    grower_id UUID REFERENCES growers(id),
    contract_id UUID REFERENCES grower_contracts(id) ON DELETE SET NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    delivery_date DATE DEFAULT CURRENT_DATE,
    volume_tonnes DECIMAL(12,2),
    price_per_tonne DECIMAL(12,2),
    quality_grade TEXT,
    value_usd DECIMAL(14,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deliveries_grower ON deliveries(grower_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_contract ON deliveries(contract_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_tenant ON deliveries(tenant_id);
