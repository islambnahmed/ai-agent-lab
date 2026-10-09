"""Seven-session historical forecast comparison. Usage: python script.py date_close.csv
Input CSV columns: date,close. GC=F and XAU/USD must be evaluated separately.
Retrospective scores do not prove real-world predictive accuracy.
"""
import csv, datetime as dt, math, statistics, sys
H, L = 7, 20
RULES = {'naive': 0, 'damped_momentum': .25, 'full_momentum': 1, 'mean_reversion': -.25}

def load(path):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ['date', 'close']:
            raise ValueError('Expected date,close CSV')
        rows = []
        for row in reader:
            date, price = dt.date.fromisoformat(row['date']), float(row['close'])
            if date.weekday() > 4 or not math.isfinite(price) or price <= 0:
                raise ValueError('Invalid row')
            if rows and date <= rows[-1][0]:
                raise ValueError('Dates must increase')
            rows.append((date, price))
    return rows

def evaluate(rows, start='2026-01-02', phase=0):
    if not 0 <= phase < H:
        raise ValueError('Invalid phase')
    first = next((i for i, (date, _) in enumerate(rows) if str(date) >= start), len(rows))
    first = max(first, L) + phase
    errors = {name: [] for name in RULES}
    for i in range(first, len(rows) - H, H):
        last, past, actual = rows[i][1], rows[i-L][1], rows[i+H][1]
        for name, alpha in RULES.items():
            predicted = round(last * math.exp(alpha * H / L * math.log(last / past)), 2)
            errors[name].append(abs(actual - predicted))
    if not errors['naive']:
        raise ValueError('No complete forecast horizons')
    baseline = statistics.mean(errors['naive'])
    return {name: {'mae': round(statistics.mean(vals), 2),
                   'skill_pct': round(100 * (1 - statistics.mean(vals) / baseline), 2)}
            for name, vals in errors.items()}

if __name__ == '__main__':
    rows = load(sys.argv[1])
    for phase in range(H):
        print('phase', phase, evaluate(rows, phase=phase))
