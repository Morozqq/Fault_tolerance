from datetime import datetime
import csv, json

TRANSACTIONS = [
    ("T001",12000,"None"),("T002",25000,"Network"),("T003",8000,"None"),
    ("T004",45000,"Timeout"),("T005",13000,"None"),("T006",70000,"Database"),
    ("T007",9000,"None"),("T008",31000,"Network"),("T009",15000,"None"),
    ("T010",50000,"Timeout"),("T011",6000,"None"),("T012",80000,"Database"),
    ("T013",11000,"None"),("T014",22000,"None"),("T015",40000,"Network")
]

def attempt(failure, n):
    if failure == "None": return "Success"
    if failure == "Network": return "Fail" if n == 1 else "Success"
    if failure == "Timeout": return "Fail" if n < 3 else "Success"
    if failure == "Database": return "Fail"
    return "Fail"

def run_baseline():
    successful, amount, attempted = [], 0, 0
    for tid, value, failure in TRANSACTIONS:
        attempted += 1
        if failure != "None": break
        successful.append(tid); amount += value
    total = sum(v for _,v,_ in TRANSACTIONS)
    return {"attempted":attempted, "successful":len(successful),
            "lost_transactions":len(TRANSACTIONS)-len(successful),
            "processed_amount":amount, "lost_amount":total-amount}

def run_fault_tolerant():
    log=[]; ids=[]; amount=0; cp_ids=[]; cp_amount=0
    checkpoints=[]; rollbacks=[]
    for tid,value,failure in TRANSACTIONS:
        max_attempts={"None":1,"Network":2,"Timeout":3,"Database":3}[failure]
        for n in range(1,max_attempts+1):
            result=attempt(failure,n)
            if result=="Success":
                action,final="Process and record","Success"
            elif failure=="Database" and n==3:
                action,final="Rollback to latest checkpoint","Rollback"
            else:
                action,final="Retry","Fail"
            log.append([datetime.now().astimezone().isoformat(timespec="seconds"),
                        tid,n,failure,action,final])
            if final in ("Success","Rollback"): break
        if final=="Success":
            ids.append(tid); amount+=value
            if len(ids)%5==0:
                cp_ids=ids.copy(); cp_amount=amount
                checkpoints.append({
                    "checkpoint":f"CP{len(checkpoints)+1}",
                    "successful_transactions":len(ids),
                    "total_amount":amount,
                    "state_saved":", ".join(ids)})
        else:
            ids=cp_ids.copy(); amount=cp_amount
            rollbacks.append(tid)
    return ids,amount,checkpoints,rollbacks,log

if __name__=="__main__":
    baseline=run_baseline()
    ids,amount,checkpoints,rollbacks,log=run_fault_tolerant()
    with open("attempt_log.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["timestamp","transaction","attempt","failure","action","result"]); w.writerows(log)
    total=sum(v for _,v,_ in TRANSACTIONS)
    summary={"baseline":baseline,"fault_tolerant":{
        "successful":len(ids),"lost_transactions":len(TRANSACTIONS)-len(ids),
        "processed_amount":amount,"lost_amount":total-amount,
        "retry_attempts":sum(1 for r in log if r[4]=="Retry"),
        "rollbacks":len(rollbacks),"checkpoints":checkpoints}}
    with open("execution_summary.json","w",encoding="utf-8") as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
