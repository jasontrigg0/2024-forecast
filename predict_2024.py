import csv
import numpy
import datetime
import math
import json
import scipy.stats
import random

#need an estimate of how reliable polls are over time
#estimate of polling errors overall

#maintain state offsets
#state estimate is combination of federal and state polling

#National average SD is about 3
#after accounting for the national polling error
#State SDs are about 3.6
#see https://fivethirtyeight.com/features/the-polls-werent-great-but-thats-pretty-normal/
NATIONAL_POLLING_SD = .03
STATE_POLLING_SD = .036 #after accounting for the national polling SD
POLL_HALFLIFE_DAYS = 7

#offsets calculated from 2020 presidential election
ELECTORAL_COLLEGE_INFO = {
    "California": { "ev": 54, "offset": .2470, "votes": 17501380 },
    "Texas": { "ev": 40, "offset": -.1004, "votes": 11315056 },
    "Florida": { "ev": 30, "offset": -.0782, "votes": 11067456 },
    "New York": { "ev": 28, "offset": .1867, "votes": 8616861 },
    "Illinois": { "ev": 19, "offset": .1253, "votes": 6033744 },
    "Pennsylvania": { "ev": 19, "offset": -.0330, "votes": 6936976 },
    "Ohio": { "ev": 17, "offset": -.1249, "votes": 5922202 },
    "Georgia": { "ev": 16, "offset": -.0422, "votes": 4999960 },
    "North Carolina": { "ev": 16, "offset": -.0581, "votes": 5524804 },
    "Michigan": { "ev": 15, "offset": -.0168, "votes": 5539302 },
    "New Jersey": { "ev": 14, "offset": .1148, "votes": 4549457 },
    "Virginia": { "ev": 13, "offset": .0565, "votes": 4460524 },
    "Washington": { "ev": 12, "offset": .1474, "votes": 4087631 },
    "Arizona": { "ev": 11, "offset" : -.0415, "votes": 3387326 },
    "Indiana": { "ev": 11, "offset": -.2053, "votes": 3033210 },
    "Massachusetts": { "ev": 11, "offset": .2900, "votes": 3631402 },
    "Tennessee": { "ev": 11, "offset": -.2767, "votes": 3053851 },
    "Colorado": { "ev": 10, "offset": .0904, "votes": 3256980 },
    "Maryland": { "ev": 10, "offset": .2875, "votes": 3037030 },
    "Minnesota": { "ev": 10, "offset": .0265, "votes": 3277171 },
    "Missouri": { "ev": 10, "offset": -.1985, "votes": 3025962 },
    "Wisconsin": { "ev": 10, "offset": -.0383, "votes": 3298041 },
    "Alabama": { "ev": 9, "offset": -.2992, "votes": 2323282 },
    "South Carolina": { "ev": 9, "offset": -.1614, "votes": 2513329 },
    "Kentucky": { "ev": 8, "offset": -.3040, "votes": 2136768 },
    "Louisiana": { "ev": 8, "offset": -.2307, "votes": 2148062 },
    "Oregon": { "ev": 8, "offset": .1163, "votes": 2374321 },
    "Connecticut": { "ev": 7, "offset": .1561, "votes": 1823857 },
    "Oklahoma": { "ev": 7, "offset": -.3755, "votes": 1560699 },
    "Arkansas": { "ev": 6, "offset": -.3208, "votes": 1219069 },
    "Iowa": { "ev": 6, "offset": -.1266, "votes": 1690871 },
    "Kansas": { "ev": 6, "offset": -.1910, "votes": 1373986 },
    "Mississippi": { "ev": 6, "offset": -.2101, "votes": 1313759 },
    "Nevada": { "ev": 6, "offset": -.0207, "votes": 1405376 },
    "Utah": { "ev": 6, "offset": -.2494, "votes": 1488289 },
    "New Mexico": { "ev": 5, "offset": .0633, "votes": 923965 },
    "Hawaii": { "ev": 4, "offset": .2500, "votes": 574469 },
    "Idaho": { "ev": 4, "offset": -.3523, "votes": 867934 },
    "Montana": { "ev": 4, "offset": -.2083, "votes": 603674 },
    "New Hampshire": { "ev": 4, "offset": .0289, "votes": 806205 },
    "Rhode Island": { "ev": 4, "offset": .1631, "votes": 517757 },
    "West Virginia": { "ev": 4, "offset": -.4339, "votes": 794731 },
    "Alaska": { "ev": 3, "offset": -.1452, "votes": 359530 },
    "Delaware": { "ev": 3, "offset": .1451, "votes": 504346 },
    "District of Columbia": { "ev": 3, "offset": .8229, "votes": 344356 },
    "North Dakota": { "ev": 3, "offset": -.3780, "votes": 362024 },
    "South Dakota": { "ev": 3, "offset": -.3062, "votes": 422609 },
    "Vermont": { "ev": 3, "offset": .3095, "votes": 367428 },
    "Wyoming": { "ev": 3, "offset": -.4784, "votes": 276765 },
    "Nebraska": { "ev": 2, "offset": -.2352, "districts": ["NE-1", "NE-2", "NE-3"], "votes": 956383 }, #plus three more EV, one for the winner of each district
    "Maine": { "ev": 2, "offset": .0461, "districts": ["ME-1", "ME-2"], "votes": 819461 }, #plus two more EV, one for the winner of each district
    "ME-1": { "ev": 1, "offset": .1863, "type": "district", "votes": 443112 },
    "ME-2": { "ev": 1, "offset": -.1190, "type": "district", "votes": 376349 },
    "NE-1": { "ev": 1, "offset": -.1938, "type": "district", "votes": 321886 },
    "NE-2": { "ev": 1, "offset": .0204, "type": "district", "votes": 339666},
    "NE-3": { "ev": 1, "offset": -.5748, "type": "district", "votes": 294831 },
}

ALL_STATES = [x for x in ELECTORAL_COLLEGE_INFO if not ELECTORAL_COLLEGE_INFO[x].get("type") == "district"]
ALL_DISTRICTS = [x for x in ELECTORAL_COLLEGE_INFO if ELECTORAL_COLLEGE_INFO[x].get("type") == "district"]

def group_by(l, fn):
    m = {}
    for x in l:
        k = fn(x)
        m.setdefault(k,[])
        m[k].append(x)
    return m

def calculate_national_polling_average():
    with open("president_polls.csv") as f:
        reader = csv.DictReader(f)
        all_rows = [row for row in reader]
        all_rows = [r for r in all_rows if r["state"] == ""]
        all_questions = list(group_by(all_rows, lambda x: x["question_id"]).values())
        all_questions.sort(reverse=True, key=lambda x: datetime.datetime.strptime(x[0]["created_at"],"%m/%d/%y %H:%M"))
        def is_harris_trump(q): return [res for res in q if res["candidate_id"] == "16661"] and [res for res in q if res["candidate_id"] == "16651"]
        all_questions = [q for q in all_questions if is_harris_trump(q)]
        candidate_average_info = {}
        for question in all_questions:
            for result in question:
                candidate_average_info.setdefault(result["candidate_name"],{"weight": 0, "total": 0})
                info = candidate_average_info[result["candidate_name"]]
                today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                question_time = datetime.datetime.strptime(result["end_date"],"%m/%d/%y")
                weight = math.exp(-math.log(2) * (today - question_time).days / POLL_HALFLIFE_DAYS)
                info["weight"] += weight
                info["total"] += weight * float(result["pct"])
        #TODO: remove candidates who have dropped out
        for candidate in candidate_average_info:
            candidate_average_info[candidate]["avg"] = candidate_average_info[candidate]["total"] / candidate_average_info[candidate]["weight"]
    return candidate_average_info

def calculate_state_polling_averages():
    pass

def simulate_election_outcomes(national_margin, sim_cnt):
    all_simulations = []
    
    for i in range(sim_cnt):
        national_polling_error = int(numpy.random.normal(0,NATIONAL_POLLING_SD,1))
        state_polling_errors = numpy.random.normal(0,STATE_POLLING_SD,51)

        #TODO: zeroing the state errors here will decrease the effective SD a bit
        #but don't think it matters
        state_polling_errors -= sum(state_polling_errors) / len(state_polling_errors)

        ec_results = {}

        for i,state in enumerate(ALL_STATES):
            ec_results[state] = national_margin + national_polling_error + state_polling_errors[i] + ELECTORAL_COLLEGE_INFO[state]["offset"]
            districts = ELECTORAL_COLLEGE_INFO[state].get("districts", [])
            for district in districts:
                ec_results[district] = national_margin + national_polling_error + state_polling_errors[i] + ELECTORAL_COLLEGE_INFO[district]["offset"]
                    
        simulation_results = {"harris": 0, "trump": 0, "ec_results": ec_results}
        for res in ec_results:
            if ec_results[res] > 0:
                simulation_results["harris"] += ELECTORAL_COLLEGE_INFO[res]["ev"]
            else:
                simulation_results["trump"] += ELECTORAL_COLLEGE_INFO[res]["ev"]

        #setting ties as 85% to trump because republicans are likely to win a majority of state delegations
        #https://www.270towin.com/2024-house-election/state-by-state/consensus-2024-house-forecast
        TRUMP_TIE_ODDS = 0.85
        simulation_results["tiebreak"] = "trump" if random.random() < TRUMP_TIE_ODDS else "harris"
        simulation_results["ec_margin"] = (simulation_results["harris"] - simulation_results["trump"]) + (0.01 if simulation_results["tiebreak"] == "harris" else -0.01)
        
        DEBUG_TIES = False
        if DEBUG_TIES and simulation_results["harris"] == simulation_results["trump"]:
            print([(x,ec_results[x]) for x in ec_results if abs(ec_results[x]) < 0.1])
            raise

        #calculate tipping point region
        sorted_ec_results = sorted([x for x in ec_results], key = lambda x: -1*ec_results[x])
        running_total = (0.01 if simulation_results["tiebreak"] == "harris" else -0.01)
        for ec_region in sorted_ec_results:
            running_total += ELECTORAL_COLLEGE_INFO[ec_region]["ev"]
            if running_total > 269:
                simulation_results["tipping_point"] = ec_region
                break
            
        all_simulations.append(simulation_results)
        
    return all_simulations

#how well can we predict upcoming polls?
def test():
    pass

if __name__ == "__main__":
    national_polling_average = calculate_national_polling_average()
    national_margin = (national_polling_average["Kamala Harris"]["avg"] - national_polling_average["Donald Trump"]["avg"]) / 100

    #test sensitivity to adjusting margins slightly
    #national_margin += 0.02 #0.0025

    SIMULATION_CNT = 100000
    all_simulations = simulate_election_outcomes(national_margin, SIMULATION_CNT)

    pred = {}

    pred["odds"] = {"harris": len([sim for sim in all_simulations if sim["ec_margin"] > 0]) / SIMULATION_CNT, "trump": len([sim for sim in all_simulations if sim["ec_margin"] < 0]) / SIMULATION_CNT}

    harris_ec_votes = sum(x["harris"] for x in all_simulations) / SIMULATION_CNT
    trump_ec_votes = sum(x["trump"] for x in all_simulations) / SIMULATION_CNT
    pred["ec_votes"] = {"harris": harris_ec_votes, "trump": trump_ec_votes}

    pred["state"] = {}

    for ec_region in ELECTORAL_COLLEGE_INFO:
        pred["state"].setdefault(ec_region,{})
        pred["state"][ec_region]["harris"] = len([x for x in all_simulations if x["ec_results"][ec_region] > 0]) / SIMULATION_CNT
        pred["state"][ec_region]["trump"] = len([x for x in all_simulations if x["ec_results"][ec_region] < 0]) / SIMULATION_CNT

        #critical regions are those that the winning party had to carry or else would have lost the election
        carried_by_winner = lambda sim: sim["ec_margin"] * sim["ec_results"][ec_region] >= 0
        is_critical_region = lambda sim: carried_by_winner(sim) and abs(sim["ec_margin"]) < 2*ELECTORAL_COLLEGE_INFO[ec_region]["ev"]
        critical_margins = []
        for sim in all_simulations:
            if is_critical_region(sim):
                critical_margins.append(sim["ec_results"][ec_region])

        pred["state"][ec_region]["tipping_point"] = len([sim for sim in all_simulations if sim["tipping_point"] == ec_region]) / SIMULATION_CNT
        
        avg = numpy.mean(critical_margins)
        sd = numpy.std(critical_margins)
        odds_critical = len(critical_margins) / SIMULATION_CNT
        # if ec_region in ["Pennsylvania", "Nevada", "Florida", "NE-2", "Texas"]:
        #     print(ec_region, avg, sd, scipy.stats.norm(avg, sd).pdf(0), odds_critical, (ELECTORAL_COLLEGE_INFO[ec_region]["votes"] / 1e6))
        pred["state"][ec_region]["raw_value"] = scipy.stats.norm(avg, sd).pdf(0) * odds_critical / (ELECTORAL_COLLEGE_INFO[ec_region]["votes"] / 1e6)

    avg_vote_value = sum([pred["state"][state]["raw_value"] * ELECTORAL_COLLEGE_INFO[state]["votes"] for state in ALL_STATES]) / sum([ELECTORAL_COLLEGE_INFO[state]["votes"] for state in ALL_STATES])
    for ec_region in ELECTORAL_COLLEGE_INFO:
        pred["state"][ec_region]["normed_value"] = pred["state"][ec_region]["raw_value"] / avg_vote_value

        # if pred["state"][ec_region]["normed_value"] > 0.5:
        #     print(ec_region, pred["state"][ec_region]["normed_value"])
    
        
    with open('pred.json', 'w', encoding='utf-8') as f:
        json.dump(pred, f, ensure_ascii=False, indent=4)
        
