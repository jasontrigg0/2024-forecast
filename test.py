import scipy.stats
import copy

if __name__ == "__main__":
    #start with some priors of various Trump biases
    priors = [
        {"mean":-0.04, "prob": .03},
        {"mean":-0.03, "prob": .06},
        {"mean":-0.02, "prob": .11},
        {"mean":-0.01, "prob": .17},
        {"mean": 0.00, "prob": .26},
        {"mean": 0.01, "prob": .17},
        {"mean": 0.02, "prob": .11},
        {"mean": 0.03, "prob": .06},
        {"mean": 0.04, "prob": .03}
    ]

    swing_probs = copy.deepcopy(priors)
    
    #swing state miss
    #2016: 4%
    #2020: 3.5%
    for x in swing_probs:
        mean = x["mean"]
        x["prob"] *= scipy.stats.norm(mean, 0.03).pdf(-0.04)
        x["prob"] *= scipy.stats.norm(mean, 0.03).pdf(-0.035)

    total = sum([i["prob"] for i in swing_probs])
    for i in swing_probs:
        i["prob"] /= total

    print("Swing state avg: ", sum([i["prob"] * i["mean"] for i in swing_probs]))
    #result: 1.6%


    
    natl_probs = copy.deepcopy(priors)
    
    #national miss
    #2016: 1.8%
    #2020: 3.9%
    for x in natl_probs:
        mean = x["mean"]
        x["prob"] *= scipy.stats.norm(mean, 0.03).pdf(-0.018)
        x["prob"] *= scipy.stats.norm(mean, 0.03).pdf(-0.039)
        
    total = sum([i["prob"] for i in natl_probs])
    for i in natl_probs:
        i["prob"] /= total

    print("Natl avg: ", sum([i["prob"] * i["mean"] for i in natl_probs]))
    #result: 1.2%
