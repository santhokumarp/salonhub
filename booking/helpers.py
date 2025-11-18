from datetime import datetime, date

def compute_required_slot_master_ids(start_slot_master, slot_masters_ordered, required_minutes):
    """
    Given a starting SlotMaster and a list of ordered active SlotMasters,
    return list of consecutive slot_master ids whose total minutes >= required_minutes.
    """
    ids = []
    total = 0
    found_start = False

    for sm in slot_masters_ordered:
        if not found_start:
            if sm.id == start_slot_master.id:
                found_start = True
            else:
                continue

        start_dt = datetime.combine(date.today(), sm.start_time)
        end_dt = datetime.combine(date.today(), sm.end_time)

        minutes = int((end_dt - start_dt).total_seconds() / 60)
        ids.append(sm.id)
        total += minutes

        if total >= required_minutes:
            break

    return ids if total >= required_minutes else None
