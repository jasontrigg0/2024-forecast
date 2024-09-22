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

POLL_HALFLIFE_DAYS = 14
BASELINE_WEIGHT = 1 / (1 - 2**(-1/POLL_HALFLIFE_DAYS))

#TODO: how to balance fundamentals vs polling early in the election
ELECTION_INFO = {
    2024: {
        "election_date": "11/5/24",
        "prev_offset": "offset2020"
    },
    2020: {
        "election_date": "11/3/20",
        "national_margin": .0446,
        "offset": "offset2020",
        "prev_offset": "offset2016"
    },
    2016: {
        "election_date": "11/8/16",
        "national_margin": .0210,
        "offset": "offset2016",
        "prev_offset": "offset2012"
    },
    2012: {
        "national_margin": .0386
    }
}

#TODO: factor in education trends here?
ELECTORAL_COLLEGE_INFO = {
    "California": { "ev": 54, "offset2020": .2470, "offset2016": .2801, "offset2012": .1926, "votes": 17501380 },
    "Texas": { "ev": 40, "offset2020": -.1004, "offset2016": -.1109, "offset2012": -.1965, "votes": 11315056 },
    "Florida": { "ev": 30, "offset2020": -.0782, "offset2016": -.0330, "offset2012": -.0298, "votes": 11067456 },
    "New York": { "ev": 28, "offset2020": .1867, "offset2016": .2039, "offset2012": .2432, "votes": 8616861 },
    "Illinois": { "ev": 19, "offset2020": .1253, "offset2016": .1496, "offset2012": .1301, "votes": 6033744 },
    "Pennsylvania": { "ev": 19, "offset2020": -.0330, "offset2016": -.0282, "offset2012": .0152, "votes": 6936976 },
    "Ohio": { "ev": 17, "offset2020": -.1249, "offset2016": -.1023, "offset2012": -.0088, "votes": 5922202 },
    "Georgia": { "ev": 16, "offset2020": -.0422, "offset2016": -.0723, "offset2012": -.1168, "votes": 4999960 },
    "North Carolina": { "ev": 16, "offset2020": -.0581, "offset2016": -.0576, "offset2012": -.0590, "votes": 5524804 },
    "Michigan": { "ev": 15, "offset2020": -.0168, "offset2016": -.0233, "offset2012": .0564, "votes": 5539302 },
    "New Jersey": { "ev": 14, "offset2020": .1148, "offset2016": .1200, "offset2012": .1393, "votes": 4549457 },
    "Virginia": { "ev": 13, "offset2020": .0565, "offset2016": .0322, "offset2012": .0002, "votes": 4460524 },
    "Washington": { "ev": 12, "offset2020": .1474, "offset2016": .1361, "offset2012": .1101, "votes": 4087631 },
    "Arizona": { "ev": 11, "offset2020" : -.0415, "offset2016": -.0560, "offset2012": -.1292, "votes": 3387326 },
    "Indiana": { "ev": 11, "offset2020": -.2053, "offset2016": -.2127, "offset2012": -.1406, "votes": 3033210 },
    "Massachusetts": { "ev": 11, "offset2020": .2900, "offset2016": .2510, "offset2012": .1928, "votes": 3631402 },
    "Tennessee": { "ev": 11, "offset2020": -.2767, "offset2016": -.2811, "offset2012": -.2426, "votes": 3053851 },
    "Colorado": { "ev": 10, "offset2020": .0904, "offset2016": .0281, "offset2012": .0150, "votes": 3256980 },
    "Maryland": { "ev": 10, "offset2020": .2875, "offset2016": .2432, "offset2012": .2221, "votes": 3037030 },
    "Minnesota": { "ev": 10, "offset2020": .0265, "offset2016": -.0058, "offset2012": .0383, "votes": 3277171 },
    "Missouri": { "ev": 10, "offset2020": -.1985, "offset2016": -.2074, "offset2012": -.1324, "votes": 3025962 },
    "Wisconsin": { "ev": 10, "offset2020": -.0383, "offset2016": -.0287, "offset2012": .0308, "votes": 3298041 },
    "Alabama": { "ev": 9, "offset2020": -.2992, "offset2016": -.2983, "offset2012": -.2605, "votes": 2323282 },
    "South Carolina": { "ev": 9, "offset2020": -.1614, "offset2016": -.1637, "offset2012": -.1433, "votes": 2513329 },
    "Kentucky": { "ev": 8, "offset2020": -.3040, "offset2016": -.3194, "offset2012": -.2655, "votes": 2136768 },
    "Louisiana": { "ev": 8, "offset2020": -.2307, "offset2016": -.2174, "offset2012": -.2106, "votes": 2148062 },
    "Oregon": { "ev": 8, "offset2020": .1163, "offset2016": .0888, "offset2012": .0823, "votes": 2374321 },
    "Connecticut": { "ev": 7, "offset2020": .1561, "offset2016": .1154, "offset2012": .1347, "votes": 1823857 },
    "Oklahoma": { "ev": 7, "offset2020": -.3755, "offset2016": -.3849, "offset2012": -.3730, "votes": 1560699 },
    "Arkansas": { "ev": 6, "offset2020": -.3208, "offset2016": -.2902, "offset2012": -.2755, "votes": 1219069 },
    "Iowa": { "ev": 6, "offset2020": -.1266, "offset2016": -.1151, "offset2012": .0195, "votes": 1690871 },
    "Kansas": { "ev": 6, "offset2020": -.1910, "offset2016": -.2270, "offset2012": -.2557, "votes": 1373986 },
    "Mississippi": { "ev": 6, "offset2020": -.2101, "offset2016": -.1993, "offset2012": -.1536, "votes": 1313759 },
    "Nevada": { "ev": 6, "offset2020": -.0207, "offset2016": .0032, "offset2012": .0282, "votes": 1405376 },
    "Utah": { "ev": 6, "offset2020": -.2494, "offset2016": -.2018, "offset2012": -.5179, "votes": 1488289 },
    "New Mexico": { "ev": 5, "offset2020": .0633, "offset2016": .0611, "offset2012": .0629, "votes": 923965 },
    "Hawaii": { "ev": 4, "offset2020": .2500, "offset2016": .3008, "offset2012": .3885, "votes": 574469 },
    "Idaho": { "ev": 4, "offset2020": -.3523, "offset2016": -.3387, "offset2012": -.3555, "votes": 867934 },
    "Montana": { "ev": 4, "offset2020": -.2083, "offset2016": -.2252, "offset2012": -.1751, "votes": 603674 },
    "New Hampshire": { "ev": 4, "offset2020": .0289, "offset2016": -.0173, "offset2012": .0172, "votes": 806205 },
    "Rhode Island": { "ev": 4, "offset2020": .1631, "offset2016": .1341, "offset2012": .2360, "votes": 517757 },
    "West Virginia": { "ev": 4, "offset2020": -.4339, "offset2016": -.4417, "offset2012": -.3062, "votes": 794731 },
    "Alaska": { "ev": 3, "offset2020": -.1452, "offset2016": -.1683, "offset2012": -.1785, "votes": 359530 },
    "Delaware": { "ev": 3, "offset2020": .1451, "offset2016": .0927, "offset2012": .1477, "votes": 504346 },
    "District of Columbia": { "ev": 3, "offset2020": .8229, "offset2016": .8467, "offset2012": .7977, "votes": 344356 },
    "North Dakota": { "ev": 3, "offset2020": -.3780, "offset2016": -.3783, "offset2012": -.2348, "votes": 362024 },
    "South Dakota": { "ev": 3, "offset2020": -.3062, "offset2016": -.3189, "offset2012": -.2188, "votes": 422609 },
    "Vermont": { "ev": 3, "offset2020": .3095, "offset2016": .2431, "offset2012": .3174, "votes": 367428 },
    "Wyoming": { "ev": 3, "offset2020": -.4784, "offset2016": -.4839, "offset2012": -.4468, "votes": 276765 },
    "Nebraska": { "ev": 2, "offset2020": -.2352, "offset2016": -.2715, "offset2012": -.2563, "districts": ["NE-1", "NE-2", "NE-3"], "votes": 956383 }, #plus three more EV, one for the winner of each district
    "Maine": { "ev": 2, "offset2020": .0461, "offset2016": .0086, "offset2012": .1143, "districts": ["ME-1", "ME-2"], "votes": 819461 }, #plus two more EV, one for the winner of each district
    "ME-1": { "ev": 1, "offset2020": .1863, "offset2016": .1271, "offset2012": .1753, "type": "district", "votes": 443112 },
    "ME-2": { "ev": 1, "offset2020": -.1190, "offset2016": -.1239, "offset2012": .0470, "type": "district", "votes": 376349 },
    "NE-1": { "ev": 1, "offset2020": -.1938, "offset2016": -.2282, "offset2012": -.2046, "type": "district", "votes": 321886 },
    "NE-2": { "ev": 1, "offset2020": .0204, "offset2016": -.0434, "offset2012": -.1101, "type": "district", "votes": 339666},
    "NE-3": { "ev": 1, "offset2020": -.5748, "offset2016": -.5629, "offset2012": -.4627, "type": "district", "votes": 294831 },
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

def preprocess_polling_2016():
    with open("president_general_polls_2016.csv") as f:
        reader = csv.DictReader(f)
        all_rows = list([row for row in reader if row["type"] == "polls-only"])
        for row in all_rows:
            base = {
                "created_at": row["createddate"] + " 00:00",
                "state": "" if row["state"] == "U.S." else row["state"], #to match 2020 and 2024 data
                "poll_wt": row["poll_wt"],
                "population": row["population"],
                "end_date": row["enddate"].replace("201","1"), #convert YYYY -> YY like 2016 -> 16
                "question_id": row["question_id"],
            }
            yield {
                **base,
                "party": "DEM",
                "pct": row["rawpoll_clinton"]
            }
            yield {
                **base,
                "party": "REP",
                "pct": row["rawpoll_trump"]
            }
            if row["rawpoll_johnson"]:
                yield {
                    **base,
                    "party": "LIB",
                    "pct": row["rawpoll_johnson"]
                }
            
def calculate_polling_averages(year, test_datetime, halflife):
    if year == 2016:
        all_rows = list(preprocess_polling_2016())
    elif year == 2020:
        with open("president_polls_2020.csv") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
    elif year == 2024:
        with open("president_polls.csv") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
    else:
        raise
        
    for row in all_rows:
        row["region"] = row["state"] if row["state"] else "national"
        region_mapping = {
            "Maine CD-1": "ME-1",
            "Maine CD-2": "ME-2",
            "Nebraska CD-1": "NE-1",
            "Nebraska CD-2": "NE-2",
            "Nebraska CD-3": "NE-3",
        }
        if row["region"] in region_mapping:
            row["region"] = region_mapping[row["region"]]

    all_questions = list(group_by(all_rows, lambda x: x["question_id"]).values())
    
    all_questions.sort(reverse=True, key=lambda x: datetime.datetime.strptime(x[0]["created_at"],"%m/%d/%y %H:%M"))

    get_end_date = lambda q: datetime.datetime.strptime(q["end_date"],"%m/%d/%y")

    region_to_polling_average_info = {}
    for question in all_questions:
        polling_average_info = region_to_polling_average_info.setdefault(question[0]["region"],{})
        for result in question:
            question_time = get_end_date(result)
            if question_time > test_datetime: continue
            polling_average_info.setdefault(result["party"],{"weight": 0, "total": 0})
            info = polling_average_info[result["party"]]
            weight = math.exp(-math.log(2) * (test_datetime - question_time).days / halflife) # * (1 + 100*(result["population"] == "lv"))
            info["weight"] += weight
            info["total"] += weight * float(result["pct"])
    #TODO: remove candidates who have dropped out
    for region in region_to_polling_average_info:
        polling_average_info = region_to_polling_average_info[region]
        for candidate in polling_average_info:
            polling_average_info[candidate]["avg"] = polling_average_info[candidate]["total"] / polling_average_info[candidate]["weight"]
            
    return region_to_polling_average_info

def calculate_margins(polling_averages, year):
    margins = {}
    national_margin = (polling_averages["national"]["DEM"]["avg"] - polling_averages["national"]["REP"]["avg"]) / 100
    
    #test sensitivity to adjusting margins slightly
    #national_margin += -0.007 #0.0025
    print(national_margin)
    
    prev_offset_field = ELECTION_INFO[year]["prev_offset"]
    
    for region in ELECTORAL_COLLEGE_INFO:
        if region == "national": continue

        prev_offset_pred = ELECTORAL_COLLEGE_INFO[region][prev_offset_field]
        if not region in polling_averages:
            margins[region] = prev_offset_pred
        else:
            state_margin_pred = (polling_averages[region]["DEM"]["avg"] - polling_averages[region]["REP"]["avg"]) / 100
            normed_weight = polling_averages[region]["DEM"]["weight"] / BASELINE_WEIGHT
            state_offset_pred = state_margin_pred - national_margin
            margins[region] = national_margin + ((normed_weight) * state_offset_pred + 1*prev_offset_pred) / (normed_weight + 1)
    return margins

def postprocess_simulations(all_simulations):
    pred = {}

    sim_cnt = len(all_simulations)

    #NOTE: ec_margin never exactly 0 because of the tiebreak 0.1 added in the simulation
    pred["odds"] = {"DEM": len([sim for sim in all_simulations if sim["ec_margin"] > 0]) / sim_cnt, "REP": len([sim for sim in all_simulations if sim["ec_margin"] < 0]) / sim_cnt}

    dem_ec_votes = sum(x["DEM"] for x in all_simulations) / sim_cnt
    rep_ec_votes = sum(x["REP"] for x in all_simulations) / sim_cnt
    pred["ec_votes"] = {"DEM": dem_ec_votes, "REP": rep_ec_votes}

    pred["state"] = {}

    for ec_region in ELECTORAL_COLLEGE_INFO:
        pred["state"].setdefault(ec_region,{})
        pred["state"][ec_region]["DEM"] = len([x for x in all_simulations if x["ec_results"][ec_region] > 0]) / sim_cnt
        pred["state"][ec_region]["REP"] = len([x for x in all_simulations if x["ec_results"][ec_region] < 0]) / sim_cnt

        #critical regions are those that the winning party had to carry or else would have lost the election
        carried_by_winner = lambda sim: sim["ec_margin"] * sim["ec_results"][ec_region] >= 0
        is_critical_region = lambda sim: carried_by_winner(sim) and abs(sim["ec_margin"]) < 2*ELECTORAL_COLLEGE_INFO[ec_region]["ev"]
        critical_margins = []
        for sim in all_simulations:
            if is_critical_region(sim):
                critical_margins.append(sim["ec_results"][ec_region])

        pred["state"][ec_region]["tipping_point"] = len([sim for sim in all_simulations if sim["tipping_point"] == ec_region]) / sim_cnt
        
        avg = numpy.mean(critical_margins)
        sd = numpy.std(critical_margins)
        odds_critical = len(critical_margins) / sim_cnt
        # if ec_region in ["Pennsylvania", "Nevada", "Florida", "NE-2", "Texas"]:
        #     print(ec_region, avg, sd, scipy.stats.norm(avg, sd).pdf(0), odds_critical, (ELECTORAL_COLLEGE_INFO[ec_region]["votes"] / 1e6))
        pred["state"][ec_region]["raw_value"] = scipy.stats.norm(avg, sd).pdf(0) * odds_critical / (ELECTORAL_COLLEGE_INFO[ec_region]["votes"] / 1e6)

    avg_vote_value = sum([pred["state"][state]["raw_value"] * ELECTORAL_COLLEGE_INFO[state]["votes"] for state in ALL_STATES]) / sum([ELECTORAL_COLLEGE_INFO[state]["votes"] for state in ALL_STATES])
    for ec_region in ELECTORAL_COLLEGE_INFO:
        pred["state"][ec_region]["normed_value"] = pred["state"][ec_region]["raw_value"] / avg_vote_value

        # if pred["state"][ec_region]["normed_value"] > 0.5:
        #     print(ec_region, pred["state"][ec_region]["normed_value"])
    
    return pred

def calculate_daily_national_average(year):
    election_date = ELECTION_INFO[year]["election_date"]
    election_datetime = datetime.datetime.strptime(election_date, "%m/%d/%y").replace(hour=0, minute=0, second=0, microsecond=0)

    day_of_polling_averages = calculate_polling_averages(year, election_datetime, 1)
    day_of_margin = (day_of_polling_averages["national"]["DEM"]["avg"] - day_of_polling_averages["national"]["REP"]["avg"]) / 100

    err_sq = 0
    for days_before_election in range(240):
        test_datetime = election_datetime - datetime.timedelta(days=days_before_election)
    
        polling_averages = calculate_polling_averages(year, test_datetime, POLL_HALFLIFE_DAYS)
        national_margin = (polling_averages["national"]["DEM"]["avg"] - polling_averages["national"]["REP"]["avg"]) / 100

        err_sq += (national_margin - day_of_margin) ** 2
        print(test_datetime, national_margin)
    print(err_sq)
    raise

def simulate_election_outcomes(margins, days_to_election, sim_cnt, trump_bias_mode):
    #National average SD is about 3
    #after accounting for the national polling error
    #State SDs are about 3.6
    #see https://fivethirtyeight.com/features/the-polls-werent-great-but-thats-pretty-normal/
    NATIONAL_POLLING_SD = .03
    STATE_POLLING_SD = .036 #after accounting for the national polling SD

    #in the last three presidential elections national margins moved about 4-5pct in the 8 months
    #leading up to the election -> assume sd of about 6% scaling down as we approach the election
    POLL_SWING_SD = .06 * (days_to_election / 240)**0.5

    all_simulations = []
    
    for i in range(sim_cnt):
        #this is probably the big one for the election
        trump_error = 0
        if trump_bias_mode == "No Bias":
            trump_error = 0
        elif trump_bias_mode == "2%":
            trump_error = -0.02
        elif trump_bias_mode == "4%":
            trump_error = -0.04
        elif trump_bias_mode == "Blend":
            trump_error = float(numpy.random.normal(-0.02, .02, 1))
        else:
            raise
            
        poll_swing_error = float(numpy.random.normal(0, POLL_SWING_SD,1)) #gap in national margin between today and election day
        national_polling_error = float(numpy.random.normal(0,NATIONAL_POLLING_SD,1)) #gap between final polls and true national margin

        state_polling_errors = numpy.random.normal(0,STATE_POLLING_SD,51)

        #TODO: zeroing the state errors here will decrease the effective SD a bit
        #but don't think it matters
        state_polling_errors -= sum(state_polling_errors) / len(state_polling_errors)

        ec_results = {}

        for i,state in enumerate(ALL_STATES):
            total_error = poll_swing_error + national_polling_error + state_polling_errors[i] + trump_error
            ec_results[state] = margins[state] + total_error
            districts = ELECTORAL_COLLEGE_INFO[state].get("districts", [])
            for district in districts:
                ec_results[district] = margins[district] + total_error
                    
        simulation_results = {"DEM": 0, "REP": 0, "ec_results": ec_results}
        for res in ec_results:
            if ec_results[res] > 0:
                simulation_results["DEM"] += ELECTORAL_COLLEGE_INFO[res]["ev"]
            else:
                simulation_results["REP"] += ELECTORAL_COLLEGE_INFO[res]["ev"]

        #setting ties as 85% to trump because republicans are likely to win a majority of state delegations
        #https://www.270towin.com/2024-house-election/state-by-state/consensus-2024-house-forecast
        REPUBLICAN_TIE_ODDS = 0.85
        simulation_results["tiebreak"] = "REP" if random.random() < REPUBLICAN_TIE_ODDS else "DEM"
        simulation_results["ec_margin"] = (simulation_results["DEM"] - simulation_results["REP"]) + (0.01 if simulation_results["tiebreak"] == "DEM" else -0.01)
        
        DEBUG_TIES = False
        if DEBUG_TIES and abs(simulation_results["DEM"] - simulation_results["REP"]) < 1:
            print([(x,ec_results[x]) for x in ec_results if abs(ec_results[x]) < 0.1])
            raise

        #calculate tipping point region
        sorted_ec_results = sorted([x for x in ec_results], key = lambda x: -1*ec_results[x])
        running_total = (0.01 if simulation_results["tiebreak"] == "DEM" else -0.01)
        for ec_region in sorted_ec_results:
            running_total += ELECTORAL_COLLEGE_INFO[ec_region]["ev"]
            if running_total > 269:
                simulation_results["tipping_point"] = ec_region
                break
            
        all_simulations.append(simulation_results)
        
    return all_simulations

def evaluate_historical(year):
    election_date = ELECTION_INFO[year]["election_date"]
    election_datetime = datetime.datetime.strptime(election_date, "%m/%d/%y").replace(hour=0, minute=0, second=0, microsecond=0)
    polling_averages = calculate_polling_averages(year, election_datetime, POLL_HALFLIFE_DAYS)
    
    national_margin = (polling_averages["national"]["DEM"]["avg"] - polling_averages["national"]["REP"]["avg"]) / 100

    overall_state_err_sq = 0
    overall_natl_err_sq = 0
    state_err_sq = 0
    natl_err_sq = 0
    mix_err_sq = 0
    new_mix_err_sq = 0
    state_err_avg = 0
    natl_err_avg = 0
    cnt = 0
    
    overall_swing_state_err_sq = 0
    overall_swing_natl_err_sq = 0
    swing_state_err_sq = 0
    swing_natl_err_sq = 0
    swing_mix_err_sq = 0
    swing_new_mix_err_sq = 0
    swing_state_err_avg = 0
    swing_natl_err_avg = 0
    swing_cnt = 0
    for region in polling_averages:
        if region == "national": continue
        if not polling_averages.get(region):
            print(region)
            continue

        offset_field = ELECTION_INFO[year]["offset"]
        prev_offset_field = ELECTION_INFO[year]["prev_offset"]
        
        state_margin_pred = (polling_averages[region]["DEM"]["avg"] - polling_averages[region]["REP"]["avg"]) / 100
        natl_margin_pred = national_margin + ELECTORAL_COLLEGE_INFO[region][prev_offset_field]

        prev_offset_pred = ELECTORAL_COLLEGE_INFO[region][prev_offset_field]
        state_offset_pred = state_margin_pred - national_margin
        mix_pred = 0.5*state_offset_pred + 0.5*prev_offset_pred

        normed_weight = polling_averages[region]["DEM"]["weight"] / BASELINE_WEIGHT
        new_mix_pred = ((normed_weight) * state_offset_pred + 1*prev_offset_pred) / (normed_weight + 1)

        result = ELECTION_INFO[year]["national_margin"] + ELECTORAL_COLLEGE_INFO[region][offset_field]
        offset_result = ELECTORAL_COLLEGE_INFO[region][offset_field]
        
        overall_state_err_sq += (state_margin_pred - result) ** 2
        overall_natl_err_sq += (natl_margin_pred - result) ** 2
        state_err_sq += (state_offset_pred - offset_result) ** 2
        natl_err_sq += (prev_offset_pred - offset_result) ** 2
        mix_err_sq += (mix_pred - offset_result) ** 2
        new_mix_err_sq += (new_mix_pred - offset_result) ** 2
        state_err_avg += (state_margin_pred - result)
        natl_err_avg += (natl_margin_pred - result)
        cnt += 1
        if abs(result) < 0.1:
            print(region, offset_result, state_offset_pred, prev_offset_pred, new_mix_pred, polling_averages[region]["DEM"]["weight"], normed_weight)
            print(region, result, prev_offset_pred)
            overall_swing_state_err_sq += (state_margin_pred - result) ** 2
            overall_swing_natl_err_sq += (natl_margin_pred - result) ** 2
            swing_state_err_sq += (state_offset_pred - offset_result) ** 2
            swing_natl_err_sq += (prev_offset_pred - offset_result) ** 2
            swing_mix_err_sq += (mix_pred - offset_result) ** 2
            swing_new_mix_err_sq += (new_mix_pred - offset_result) ** 2
            swing_state_err_avg += (state_margin_pred - result)
            swing_natl_err_avg += (natl_margin_pred - result)
            swing_cnt += 1
    print("All State Offsets")
    print(state_err_sq)
    print(natl_err_sq)
    print(mix_err_sq)
    print(new_mix_err_sq)
    print("Swing State Offsets")
    print(swing_state_err_sq)
    print(swing_natl_err_sq)
    print(swing_mix_err_sq)
    print(swing_new_mix_err_sq)
    print("Overall")
    print(overall_state_err_sq)
    print(overall_natl_err_sq)
    print(overall_swing_state_err_sq)
    print(overall_swing_natl_err_sq)
    print("Totals")
    print(state_err_avg / cnt)
    print(natl_err_avg / cnt)
    print(swing_state_err_avg / swing_cnt)
    print(swing_natl_err_avg / swing_cnt)
    

def calculate_projection(year, is_election_day = False):
    election_date = ELECTION_INFO[year]["election_date"]
    election_datetime = datetime.datetime.strptime(election_date, "%m/%d/%y").replace(hour=0, minute=0, second=0, microsecond=0)

    #test_datetime = election_datetime - datetime.timedelta(days=days_before_election)

    if is_election_day:
        test_datetime = election_datetime
    else:
        test_datetime = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    
    days_before_election = (election_datetime - test_datetime).days

    polling_averages = calculate_polling_averages(year, test_datetime, POLL_HALFLIFE_DAYS)

    margins = calculate_margins(polling_averages, year)

    print(margins)
    
    pred = {}
    for trump_bias_mode in ["No Bias", "2%", "4%", "Blend"]:
        SIMULATION_CNT = 10000 #100000
        all_simulations = simulate_election_outcomes(margins, days_before_election, SIMULATION_CNT, trump_bias_mode)

        mode_results = postprocess_simulations(all_simulations)
        pred[trump_bias_mode] = mode_results
        
    with open('pred.json', 'w', encoding='utf-8') as f:
        json.dump(pred, f, ensure_ascii=False, indent=4)
        

if __name__ == "__main__":
    #calculate_daily_national_average(2024)
    #evaluate_historical(2016)
    calculate_projection(2024, False)
