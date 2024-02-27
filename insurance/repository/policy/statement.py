from sqlalchemy import text


class Statement:
    insert_policy = text("""
    insert into policy(reference, product, insurance, channel, phone, prev_global_id, downloaded, premium, cost, 
    reward, retention_reward, conditions, status, attributes, lead_reference, creator_reference, 
    period_type, period_value, actual_insurance_state, created_time, updated_time, version)
    values (:reference, :product, :insurance, :channel, :phone, :prev_global_id, :downloaded, :premium, :cost, 
    :reward, :retention_reward, :conditions, :status, :attributes,:lead_reference, :creator_reference, 
    :period_type, :period_value, :actual_insurance_state, :created_time, :updated_time, :version)
    """)

    insert_or_update_insurance_state = text("""
    insert into insurance_state(
    reference, policy_reference, begin_date, end_date, email, payment_type, redirect_url, insurance_reference, 
    global_id, status)
    values (
    :reference, :policy_reference, :begin_date, :end_date, :email, :payment_type, :redirect_url, :insurance_reference, 
    :global_id, :status
    )
    on conflict (reference) do update
    set begin_date=:begin_date,
        end_date=:end_date,
        email=:email,
        payment_type=:payment_type,
        redirect_url=:redirect_url,
        insurance_reference=:insurance_reference,
        global_id=:global_id,
        status=:status
    """)

    insert_or_update_document = text("""
    insert into fin_document(reference, insurance_state_reference, type, status)
    values (:reference, :insurance_state_reference, :type, :status)
    on conflict (reference) do update
    set status=:status
    """)

    insert_policy_status_record = text("""
    insert into policy_status_record(
    status, timestamp, policy_reference
    )
    values (
    :status, :timestamp, :policy_reference
    )
    """)

    insert_insurance_state_status_record = text("""
    insert into insurance_state_status_record(
    status, timestamp, insurance_state_reference
    )
    values (
    :status, :timestamp, :insurance_state_reference
    )
    """)

    insert_policy_insurer = text("""
    insert into insurer (reference, policy_reference, is_privileged, title)
    values (:reference, :policy_reference, :is_privileged, :title)
    """)

    insert_policy_structure = text("""
    insert into structure_item (item_reference, policy_reference, type, title, attrs)
    values (:item_reference, :policy_reference, :type, :title, :attrs)
    """)

    get_policy = text("""
    with structure as (select policy_reference,
                              json_agg(
                                      json_build_object(
                                              'item_reference', item_reference,
                                              'type', type,
                                              'title', title,
                                              'attrs', attrs
                                          )
                                  ) structure
                       from structure_item
                       where policy_reference = :reference
                       group by policy_reference),
    insurance_states as (
        with fin_documents as (
            select insurance_state_reference,
            json_agg(
                json_build_object(
                    'reference', reference,
                    'type', type,
                    'status', status
                )
            ) fin_documents
            from fin_document
            where status != 'CANCELED'
            group by insurance_state_reference
        )
        select policy_reference,
            json_agg(
                json_build_object(
                    'reference', reference,
                    'begin_date', begin_date,
                    'email', email,
                    'payment_type', payment_type,
                    'redirect_url', redirect_url,
                    'insurance_reference', insurance_reference,
                    'global_id', global_id,
                    'status', status,
                    'status_history', array []::varchar[],
                    'document_collection', coalesce(document_collection.fin_documents, '[]')
                )
            ) "insurance_states"
        from insurance_state
        left join fin_documents document_collection on document_collection.insurance_state_reference = insurance_state.reference
        where policy_reference = :reference
        group by policy_reference
    )
    
    select p.reference,
           p.product,
           p.insurance,
           p.channel,
           p.phone,
           p.prev_global_id,
           p.downloaded,
           p.premium,
           p.cost,
           p.reward,
           p.retention_reward,
           p.conditions,
           p.status,
           p.attributes,
           p.lead_reference,
           p.creator_reference,
           p.period_type,
           p.period_value,
           p.actual_insurance_state,
           p.created_time,
           p.updated_time,
           p.version,
           json_build_object(
                   'reference', i.reference,
                   'is_privileged', i.is_privileged,
                   'title', i.title
               ) insurer,
           states.insurance_states,
           strct.structure
    from policy p
             join insurance_states states on states.policy_reference = p.reference
             join structure strct on strct.policy_reference = p.reference
             join insurer i on p.reference = i.policy_reference
    where p.reference = :reference    
    """)

    get_policy_reference_by_insurance_reference = text("""
    select policy_reference
    from insurance_state
    where insurance_reference=:insurance_reference
    """)

    update_policy = text("""
    update policy
    set downloaded=:downloaded,
        premium=:premium,
        cost=:cost,
        reward=:reward,
        retention_reward=:retention_reward,
        status=:status,
        attributes=:attributes,
        actual_insurance_state=:actual_insurance_state_ref,
        version=version + 1
    where reference = :reference and version=:version
    returning *;
    """)

