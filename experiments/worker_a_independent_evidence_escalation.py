"""Selective escalation to an independent evidence channel.

Model: a cheap primary channel has a shared systematic error with probability s.
Repeating/duplicating that channel cannot repair the shared error. An independent
channel costs c observations and has error probability q. We compare:
  A) primary only
  B) always independent-check
  C) selective check on a random fraction r (a deliberately weak baseline)

The point is to make the value-of-information tradeoff explicit. Without an
observable signal correlated with shared failure, selective escalation cannot
target the bad cases; it only linearly interpolates cost and error.
"""

def outcomes(shared_error=0.05, independent_error=0.01, independent_cost=8):
    rows=[]
    for r in (0, .1, .25, .5, .75, 1):
        # primary wrong with prob s. If escalated, independent channel replaces
        # decision and is wrong with q. Escalation is not targeted because the
        # primary observations contain no marker of the shared latent failure.
        err=(1-r)*shared_error + r*independent_error
        cost=1 + r*independent_cost
        rows.append((r, err, cost))
    return rows

if __name__ == "__main__":
    print("escalation,error,expected_cost")
    for r,e,c in outcomes():
        print(f"{r:.2f},{e:.4f},{c:.2f}")
