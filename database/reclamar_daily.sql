-- ====================================================================
-- FUNCIÓN RPC ATÓMICA: public.reclamar_daily
-- ====================================================================
-- Procesa el bono diario de forma atómica a nivel de base de datos.
-- Evita condiciones de carrera y dobles cobros mediante FOR UPDATE.
-- Endurecida con SET search_path = '' y calificación explícita de esquemas.
-- ====================================================================

CREATE OR REPLACE FUNCTION public.reclamar_daily(p_telegram_id BIGINT)
RETURNS pg_catalog.jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_ultimo_daily TIMESTAMPTZ;
    v_balance BIGINT;
    v_ahora TIMESTAMPTZ := pg_catalog.clock_timestamp();
    v_cooldown CONSTANT INTERVAL := INTERVAL '24 hours';
    v_restante INTERVAL;
    v_recompensa INT;
    v_nuevo_saldo BIGINT;
    v_max_int CONSTANT BIGINT := 2147483647;
BEGIN
    -- 1. Bloqueo exclusivo de fila usando telegram_id calificado
    SELECT ultimo_daily, balance 
    INTO v_ultimo_daily, v_balance 
    FROM public.usuarios 
    WHERE telegram_id = p_telegram_id 
    FOR UPDATE;

    -- 2. Si el usuario no existe en la base de datos
    IF NOT FOUND THEN
        RETURN pg_catalog.jsonb_build_object(
            'exito', false,
            'error', 'usuario_no_encontrado'
        );
    END IF;

    -- 3. Comprobación del cooldown de 24 horas
    IF v_ultimo_daily IS NOT NULL AND (v_ahora - v_ultimo_daily) < v_cooldown THEN
        v_restante := v_cooldown - (v_ahora - v_ultimo_daily);
        RETURN pg_catalog.jsonb_build_object(
            'exito', false,
            'error', 'cooldown_activo',
            'segundos_restantes', GREATEST(0, EXTRACT(EPOCH FROM v_restante)::BIGINT)
        );
    END IF;

    -- 4. Cálculo aleatorio seguro de la recompensa (100 a 300)
    v_recompensa := pg_catalog.floor(pg_catalog.random() * (300 - 100 + 1) + 100)::INT;

    -- 5. Manejo de balance nulo y prevención de desbordamiento de INTEGER
    IF (COALESCE(v_balance, 0) + v_recompensa) > v_max_int THEN
        RETURN pg_catalog.jsonb_build_object(
            'exito', false,
            'error', 'desbordamiento_saldo'
        );
    END IF;

    v_nuevo_saldo := COALESCE(v_balance, 0) + v_recompensa;

    -- 6. Actualización atómica en la misma transacción
    UPDATE public.usuarios 
    SET ultimo_daily = v_ahora,
        balance = v_nuevo_saldo::INT
    WHERE telegram_id = p_telegram_id;

    -- 7. Retorno exitoso
    RETURN pg_catalog.jsonb_build_object(
        'exito', true,
        'recompensa', v_recompensa,
        'nuevo_saldo', v_nuevo_saldo
    );
END;
$$;

-- Propietario de la función
ALTER FUNCTION public.reclamar_daily(BIGINT) OWNER TO postgres;

-- ====================================================================
-- PERMISOS DE EJECUCIÓN (MÍNIMO PRIVILEGIO)
-- ====================================================================

-- Revocar acceso público y de roles no autenticados
REVOKE ALL ON FUNCTION public.reclamar_daily(BIGINT) FROM PUBLIC, anon, authenticated;

-- Conceder ejecución exclusivamente a service_role (backend del bot)
GRANT EXECUTE ON FUNCTION public.reclamar_daily(BIGINT) TO service_role;
