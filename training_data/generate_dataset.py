"""
generate_dataset.py

Kaj: Intent classification er jonno dataset generate kora.
Ei script template-based generator – alada alada sentence pattern
column/value/location diye bhoriye onek variation banay.

Output: intent_dataset.csv (question, intent)
"""

import csv
import random

random.seed(42)

# ---------- Subjects (100+) ----------
subjects = [
    "patients", "records", "data", "students", "customers", "rows", "entries",
    "people", "items", "transactions", "orders", "products", "employees",
    "sales", "reports", "files", "documents", "logs", "events", "tickets",
    "bookings", "flights", "hotels", "cars", "houses", "cities", "countries",
    "schools", "hospitals", "companies", "stores", "inventories", "shipments",
    "payments", "invoices", "receipts", "schedules", "tasks", "projects",
    "milestones", "bugs", "features", "issues", "requests", "responses",
    "messages", "comments", "posts", "users", "profiles", "accounts",
    "assets", "resources", "facilities", "departments", "teams", "clients",
    "partners", "vendors", "suppliers", "manufacturers", "distributors",
    "agents", "managers", "engineers", "designers", "developers", "testers",
    "analysts", "consultants", "admins", "editors", "reviewers", "approvers",
    "readers", "writers", "owners", "members", "guests", "visitors",
    "applicants", "candidates", "interviews", "assessments", "exams",
    "assignments", "submissions", "grades", "transcripts", "certificates",
    "degrees", "enrollments", "registrations", "attendance", "leaves",
    "holidays", "vacations", "expenses", "budgets", "forecasts", "targets",
    "goals", "objectives", "strategies", "plans", "actions", "outcomes"
]

# ---------- Columns (300+) ----------
columns = [
    "age", "price", "salary", "marks", "income", "score", "height", "weight",
    "temperature", "distance", "duration", "quantity", "amount", "discount",
    "tax", "rating", "rank", "level", "size", "volume", "length", "width",
    "depth", "speed", "acceleration", "force", "energy", "power", "voltage",
    "current", "resistance", "capacitance", "frequency", "wavelength",
    "density", "mass", "time", "date", "timestamp", "status", "type",
    "category", "color", "brand", "model", "version", "language", "country",
    "city", "region", "zone", "department", "team", "owner", "priority",
    "severity", "complexity", "effort", "cost", "revenue", "profit", "loss",
    "balance", "credit", "debit", "interest", "rate", "percentage",
    "fraction", "ratio", "factor", "coefficient", "index", "score",
    "grade", "rank", "percentile", "average", "median", "mode", "stddev",
    "variance", "covariance", "correlation", "regression", "prediction",
    "accuracy", "precision", "recall", "f1", "auc", "loss", "error",
    "tolerance", "capacity", "load", "usage", "consumption", "production",
    "output", "input", "throughput", "latency", "bandwidth", "storage",
    "memory", "cpu", "gpu", "disk", "network", "traffic", "requests",
    "responses", "errors", "warnings", "info", "debug", "trace", "log",
    "event", "session", "user", "device", "platform", "os", "browser",
    "referrer", "landing", "conversion", "bounce", "duration", "depth",
    "frequency", "recency", "engagement", "satisfaction", "loyalty",
    "churn", "retention", "acquisition", "activation", "revenue", "cost",
    "margin", "roi", "cpc", "cpa", "ctr", "impressions", "clicks",
    "views", "visits", "shares", "likes", "comments", "follows", "subscribers",
    "active", "inactive", "pending", "completed", "cancelled", "refunded",
    "shipped", "delivered", "returned", "open", "closed", "resolved",
    "assigned", "unassigned", "reviewed", "approved", "rejected",
    "draft", "published", "archived", "deleted", "modified", "created",
    "last_updated", "start_date", "end_date", "due_date", "delivery_date",
    "birth_date", "hire_date", "join_date", "leave_date", "graduation",
    "enrollment", "registration", "subscription", "membership", "plan",
    "tier", "level", "role", "permission", "capability", "feature",
    "module", "component", "service", "endpoint", "api", "method",
    "version", "build", "release", "patch", "hotfix", "sprint", "backlog",
    "task", "subtask", "parent", "child", "dependency", "blocker",
    "epic", "story", "requirement", "specification", "test_case",
    "test_result", "coverage", "quality", "security", "performance",
    "reliability", "availability", "scalability", "maintainability",
    "portability", "compatibility", "usability", "accessibility",
    "internationalization", "localization", "encryption", "decryption",
    "hash", "salt", "key", "certificate", "token", "session_id",
    "request_id", "trace_id", "span_id", "timestamp", "date", "datetime",
    "timezone", "offset", "duration", "interval", "frequency", "period",
    "cycle", "iteration", "phase", "stage", "step", "milestone",
    "deliverable", "artifact", "baseline", "release", "deployment",
    "environment", "cluster", "node", "pod", "container", "image",
    "volume", "network_policy", "secret", "configmap", "service_account",
    "namespace", "resource_quota", "limit", "request", "usage", "capacity",
]

# ---------- Values (200+) ----------
values = [
    "30", "50", "100", "18", "25", "60", "45", "70", "90", "120", "150",
    "200", "500", "1000", "2500", "5000", "10000", "0", "1", "2", "3", "4",
    "5", "10", "15", "20", "40", "80", "160", "320", "640", "1280",
    "true", "false", "yes", "no", "on", "off", "enabled", "disabled",
    "active", "inactive", "pending", "completed", "cancelled", "refunded",
    "shipped", "delivered", "returned", "open", "closed", "resolved",
    "assigned", "unassigned", "reviewed", "approved", "rejected",
    "draft", "published", "archived", "deleted", "modified", "created",
    "high", "medium", "low", "critical", "major", "minor", "trivial",
    "urgent", "normal", "lowest", "highest", "average", "above", "below",
    "2024-01-01", "2024-06-15", "2025-12-31", "2023-07-04", "2022-03-21",
    "2021-09-09", "2020-02-29", "2026-11-11", "2027-05-05", "2028-08-08",
    "01/01/2024", "06/15/2024", "12/31/2025", "07/04/2023", "03/21/2022",
    "09/09/2021", "02/29/2020", "11/11/2026", "05/05/2027", "08/08/2028",
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "FY2024", "FY2025",
    "red", "blue", "green", "yellow", "purple", "orange", "black",
    "white", "gray", "brown", "pink", "teal", "navy", "silver", "gold",
    "small", "medium", "large", "extra-large", "one", "two", "three",
    "four", "five", "six", "seven", "eight", "nine", "ten",
    "single", "double", "triple", "multiple", "all", "none", "some",
    "many", "few", "several", "a lot", "a little", "plenty","A","B",
]

# ---------- Locations (100+) ----------
locations = [
    "dhaka", "chittagong", "sylhet", "khulna", "rajshahi", "barisal",
    "rangpur", "mymensingh", "comilla", "noakhali", "feni", "cox's bazar",
    "tangail", "jessore", "bogra", "dinajpur", "kushtia", "faridpur",
    "satkhira", "jhalokati", "barguna", "patuakhali", "bhola", "barishal",
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
    "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
    "fort worth", "columbus", "charlotte", "san francisco", "indianapolis",
    "seattle", "denver", "washington", "boston", "el paso", "detroit",
    "nashville", "memphis", "portland", "oklahoma city", "las vegas",
    "baltimore", "milwaukee", "albuquerque", "tucson", "fresno",
    "sacramento", "kansas city", "long beach", "miami", "raleigh",
    "omaha", "tulsa", "wichita", "cleveland", "tampa", "arlington",
    "new orleans", "bakersfield", "aurora", "honolulu", "anaheim",
    "santa ana", "corpus christi", "riverside", "st. louis", "lexington",
    "stockton", "pittsburgh", "anchorage", "cincinnati", "greensboro",
    "plano", "lincoln", "orlando", "irvine", "newark", "durham",
    "chula vista", "toledo", "fort wayne", "st. paul", "buffalo",
    "london", "paris", "berlin", "madrid", "rome", "moscow", "beijing",
    "tokyo", "seoul", "mumbai", "delhi", "bangkok", "singapore",
    "sydney", "melbourne", "toronto", "vancouver", "montreal",
    "mexico city", "sao paulo", "buenos aires", "cairo", "lagos",
    "nairobi", "cape town", "dubai", "abuja", "accra", "dakar",
]

# ---------- Prefixes (30+) ----------
prefixes = [
    "", "can you ", "could you ", "please ", "i want to ", "i need to ",
    "tell me ", "show me ", "list me ", "give me ", "find me ", "get me ",
    "do you know ", "would you ", "can you please ", "could you please ",
    "i would like to ", "may i please ", "is it possible to ",
    "could i get ", "can i have ", "would you mind ", "can you kindly ",
    "i'd like to ", "i wish to ", "i'm looking for ", "i'm trying to ",
    "help me ", "assist me ", "kindly ", "please show ", "please list ",
]

# ---------- Condition phrases (extended with "exactly", "at least", etc.) ----------
# Ei condition gulo templates e use korbo. Proti condition er sathe ekta SQL operator define kore dewa better,
# kintu ei dataset generation e shudhu text pattern important; SQL generation er jonno alada logic.
condition_phrases = [
    # Equality / exact
    ("where {col} is {val}", "="),
    ("where {col} = {val}", "="),
    ("where {col} equals {val}", "="),
    ("where {col} exactly {val}", "="),
    ("with {col} exactly {val}", "="),
    ("with {col} equal to {val}", "="),
    ("{col} is {val}", "="),
    ("{col} = {val}", "="),
    ("{col} equals {val}", "="),
    ("{col} exactly {val}", "="),
    ("having {col} equal to {val}", "="),
    # Greater than
    ("where {col} > {val}", ">"),
    ("where {col} greater than {val}", ">"),
    ("where {col} more than {val}", ">"),
    ("with {col} > {val}", ">"),
    ("with {col} greater than {val}", ">"),
    ("{col} greater than {val}", ">"),
    ("{col} more than {val}", ">"),
    ("having {col} > {val}", ">"),
    # Greater than or equal
    ("where {col} >= {val}", ">="),
    ("where {col} at least {val}", ">="),
    ("with {col} >= {val}", ">="),
    ("with {col} at least {val}", ">="),
    ("{col} at least {val}", ">="),
    ("having {col} >= {val}", ">="),
    # Less than
    ("where {col} < {val}", "<"),
    ("where {col} less than {val}", "<"),
    ("where {col} fewer than {val}", "<"),
    ("with {col} < {val}", "<"),
    ("with {col} less than {val}", "<"),
    ("{col} less than {val}", "<"),
    ("{col} fewer than {val}", "<"),
    ("having {col} < {val}", "<"),
    # Less than or equal
    ("where {col} <= {val}", "<="),
    ("where {col} at most {val}", "<="),
    ("with {col} <= {val}", "<="),
    ("with {col} at most {val}", "<="),
    ("{col} at most {val}", "<="),
    ("having {col} <= {val}", "<="),
    # Not equal
    ("where {col} != {val}", "!="),
    ("where {col} not equal to {val}", "!="),
    ("where {col} is not {val}", "!="),
    ("with {col} != {val}", "!="),
    ("with {col} not {val}", "!="),
    ("{col} not {val}", "!="),
    ("having {col} != {val}", "!="),
    # Contains / text patterns
    ("where {col} contains {val}", "LIKE"),
    ("where {col} like {val}", "LIKE"),
    ("with {col} containing {val}", "LIKE"),
    # Starts with
    ("where {col} starts with {val}", "STARTS"),
    ("with {col} starting with {val}", "STARTS"),
    # Ends with
    ("where {col} ends with {val}", "ENDS"),
    ("with {col} ending with {val}", "ENDS"),
]

# ---------- Template generation function (expanded) ----------
def generate_templates(intent):
    templates = set()

    if intent == "SELECT":
        verbs = [
            "show", "show me", "show all", "show me all", "show every",
            "list", "list me", "list all", "list me all", "list every",
            "display", "display me", "display all", "display me all",
            "fetch", "fetch me", "fetch all", "fetch me all",
            "retrieve", "retrieve me", "retrieve all", "retrieve me all",
            "get", "get me", "get all", "get me all", "get every",
            "find", "find me", "find all", "find me all", "find every",
            "see", "see me", "see all", "see me all", "see every",
            "print", "print me", "print all", "print me all",
            "return", "return me", "return all", "return me all",
            "give me", "give me all", "tell me", "tell me all",
        ]
        questions = [
            "what are", "what are the", "who are", "who are the",
            "which are", "which are the", "which", "what",
        ]
        location_phrases = [
            "from {loc}", "in {loc}", "at {loc}", "located in {loc}",
            "from the {loc}", "in the {loc}", "at the {loc}"
        ]

        # Basic patterns
        for v in verbs:
            templates.add(f"{v} {{subj}}")
            templates.add(f"{v} the {{subj}}")
            templates.add(f"{v} all {{subj}}")
            templates.add(f"{v} every {{subj}}")

        # With condition phrases (using the extended list)
        for cond, _ in condition_phrases:
            for v in verbs:
                templates.add(f"{v} {{subj}} {cond}")
                templates.add(f"{v} the {{subj}} {cond}")
                templates.add(f"{v} all {{subj}} {cond}")
            for q in questions:
                templates.add(f"{q} {{subj}} {cond}")
                templates.add(f"{q} {{subj}} {cond}?")

        # With location
        for loc in location_phrases:
            for v in verbs:
                templates.add(f"{v} {{subj}} {loc}")
                templates.add(f"{v} the {{subj}} {loc}")
                templates.add(f"{v} all {{subj}} {loc}")
            for q in questions:
                templates.add(f"{q} {{subj}} {loc}")
                templates.add(f"{q} {{subj}} {loc}?")

        # Condition + location together
        for cond, _ in condition_phrases:
            for loc in location_phrases:
                for v in verbs:
                    templates.add(f"{v} {{subj}} {cond} {loc}")
                    templates.add(f"{v} the {{subj}} {cond} {loc}")
                for q in questions:
                    templates.add(f"{q} {{subj}} {cond} {loc}")
                    templates.add(f"{q} {{subj}} {cond} {loc}?")

        # Extra: "list of {subj} ..."
        templates.add("list of {subj}")
        templates.add("list of all {subj}")
        templates.add("show list of {subj}")
        templates.add("give me a list of {subj}")
        templates.add("a list of {subj}")
        templates.add("all {subj}")
        templates.add("all the {subj}")
        templates.add("every {subj}")

    elif intent == "COUNT":
        count_verbs = [
            "count", "count all", "count the", "count every",
            "how many", "how many of", "how many are there",
            "total number of", "number of", "total count of",
            "tell me how many", "show me how many",
            "give me the count of", "what is the count of",
        ]
        location_phrases = [
            "from {loc}", "in {loc}", "at {loc}", "located in {loc}",
            "from the {loc}"
        ]

        for v in count_verbs:
            templates.add(f"{v} {{subj}}")
            templates.add(f"{v} {{subj}}?")
            # Condition
            for cond, _ in condition_phrases:
                templates.add(f"{v} {{subj}} {cond}")
                templates.add(f"{v} {{subj}} {cond}?")
            # Location
            for loc in location_phrases:
                templates.add(f"{v} {{subj}} {loc}")
                templates.add(f"{v} {{subj}} {loc}?")
            # Condition + location
            for cond, _ in condition_phrases:
                for loc in location_phrases:
                    templates.add(f"{v} {{subj}} {cond} {loc}")
                    templates.add(f"{v} {{subj}} {cond} {loc}?")

        templates.add("how many {subj} are there")
        templates.add("how many {subj} exist")
        templates.add("count of {subj}")
        templates.add("count all {subj}")
        templates.add("total {subj}")
        templates.add("total number of {subj}")

    elif intent in ["AVG", "MAX", "MIN", "SUM"]:
        word_map = {
            "AVG": ["average", "mean"],
            "MAX": ["maximum", "highest", "largest", "greatest", "max"],
            "MIN": ["minimum", "lowest", "smallest", "least", "min"],
            "SUM": ["sum", "total", "add", "summation"],
        }
        words = word_map[intent]
        location_phrases = [
            "from {loc}", "in {loc}", "at {loc}"
        ]

        for w in words:
            # Basic
            templates.add(f"{w} {{col}}")
            templates.add(f"{w} of {{col}}")
            templates.add(f"the {w} of {{col}}")
            templates.add(f"what is the {w} of {{col}}")
            templates.add(f"find the {w} {{col}}")
            templates.add(f"get the {w} {{col}}")
            templates.add(f"show the {w} {{col}}")
            templates.add(f"tell me the {w} {{col}}")
            # With subject
            templates.add(f"{w} {{col}} of {{subj}}")
            templates.add(f"the {w} {{col}} of {{subj}}")
            templates.add(f"what is the {w} {{col}} of {{subj}}")
            templates.add(f"find the {w} {{col}} of {{subj}}")
            # With location
            templates.add(f"{w} {{col}} from {{loc}}")
            templates.add(f"the {w} {{col}} in {{loc}}")
            templates.add(f"what is the {w} {{col}} in {{loc}}")
            # With subject and location
            templates.add(f"{w} {{col}} of {{subj}} from {{loc}}")
            templates.add(f"the {w} {{col}} of {{subj}} in {{loc}}")
            # With condition
            for cond, _ in condition_phrases:
                templates.add(f"{w} {{col}} of {{subj}} {cond}")
                templates.add(f"the {w} {{col}} of {{subj}} {cond}")
                templates.add(f"{w} {{col}} from {{loc}} {cond}")
                templates.add(f"the {w} {{col}} from {{loc}} {cond}")
                # condition + location
                for loc in location_phrases:
                    templates.add(f"{w} {{col}} of {{subj}} {cond} {loc}")
                    templates.add(f"the {w} {{col}} of {{subj}} {cond} {loc}")

        if intent == "AVG":
        templates.update([
            "average {col}",
            "average value of {col}",
            "mean {col}",
            "mean value of {col}",
            "calculate average {col}",
            "find average {col}",
            "what is the average {col}",
            "what's the average {col}",
            "average {col} of {subj}",
            "average {col} for {subj}"
        ])

    elif intent == "MAX":
        templates.update([
            "max {col}",
            "maximum {col}",
            "highest {col}",
            "highest value of {col}",
            "largest {col}",
            "greatest {col}",
            "biggest {col}",
            "top {col}",
            "maximum value of {col}",
            "find the highest {col}",
            "find the maximum {col}",
            "show the highest {col}",
            "show the maximum {col}",
            "what is the highest {col}",
            "what is the maximum {col}",
            "most expensive {subj}",
            "costliest {subj}",
            "most costly {subj}"
        ])

    elif intent == "MIN":
        templates.update([
            "min {col}",
            "minimum {col}",
            "lowest {col}",
            "lowest value of {col}",
            "smallest {col}",
            "least {col}",
            "minimum value of {col}",
            "find the lowest {col}",
            "find the minimum {col}",
            "show the lowest {col}",
            "show the minimum {col}",
            "what is the lowest {col}",
            "what is the minimum {col}",
            "cheapest {subj}",
            "cheap {subj}",
            "least expensive {subj}",
            "most affordable {subj}",
            "lowest priced {subj}"
        ])

    elif intent == "SUM":
        templates.update([
            "sum {col}",
            "sum of {col}",
            "sum up {col}",
            "calculate sum of {col}",
            "add up {col}",
            "total {col}",
            "total value of {col}",
            "find total {col}",
            "calculate total {col}",
            "what is the total {col}",
            "what's the total {col}"
        ])

    return templates

# Generate all templates
all_templates = {}
for intent in ["SELECT", "COUNT", "AVG", "MAX", "MIN", "SUM"]:
    templates = generate_templates(intent)
    # Ensure at least 80 templates
    if len(templates) < 80:
        fallback = {
            "SELECT": ["show {subj}", "list {subj}", "get {subj}"],
            "COUNT": ["count {subj}", "how many {subj}"],
            "AVG": ["average {col}"],
            "MAX": ["maximum {col}"],
            "MIN": ["minimum {col}"],
            "SUM": ["sum {col}"],
        }
        for fb in fallback[intent]:
            templates.add(fb)
    all_templates[intent] = list(templates)
    print(f"Intent '{intent}' er {len(templates)} ta template generate kora hoyeche.")

# ---------- Generate dataset (>= 50,000 unique) ----------
pairs = []
seen = set()
target = 50000
intent_counts = {intent: 0 for intent in all_templates}

print("\nDataset generate korchi (minimum 50,000 unique example)...")

while len(pairs) < target:
    # Balanced intent selection
    intent = min(intent_counts, key=intent_counts.get)
    template = random.choice(all_templates[intent])
    # Fill placeholders
    sentence = template.format(
        subj=random.choice(subjects),
        col=random.choice(columns),
        val=random.choice(values),
        loc=random.choice(locations),
    )
    # Add prefix (60% chance)
    if random.random() < 0.6:
        prefix = random.choice(prefixes)
        sentence = prefix + sentence
    sentence = sentence.strip()
    # Avoid duplicates
    if sentence not in seen:
        seen.add(sentence)
        pairs.append((sentence, intent))
        intent_counts[intent] += 1
        if len(pairs) % 5000 == 0:
            print(f"{len(pairs)} ta unique example generate hoyeche...")

random.shuffle(pairs)

# Save CSV
with open("intent_dataset.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["question", "intent"])
    writer.writerows(pairs)

print(f"\nTotal {len(pairs)} ta example generate kora hoyeche.")
print("File: intent_dataset.csv")