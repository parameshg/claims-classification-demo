PRAGMA foreign_keys = ON;

INSERT INTO customers (customer_id, full_name) VALUES
  (1, 'Alice Morgan'),
  (2, 'Ben Carter'),
  (3, 'Chloe Singh'),
  (4, 'Daniel Okafor'),
  (5, 'Emma Walsh'),
  (6, 'Farid Rahman'),
  (7, 'Grace Liu'),
  (8, 'Henry Brooks');

INSERT INTO policies (policy_id, customer_id, cover_type, excess, start_date, end_date, exclusions) VALUES
  (1, 1, 'comprehensive',               250, '2025-06-01', '2026-05-31', '[]'),
  (2, 2, 'comprehensive',               500, '2025-09-01', '2026-08-31', '["racing","driving under the influence"]'),
  (3, 3, 'third party fire and theft',  300, '2025-07-15', '2026-07-14', '["glass damage","vandalism","weather damage"]'),
  (4, 4, 'third party only',            200, '2025-04-01', '2026-03-31', '["theft","fire","glass damage","weather damage","vandalism"]'),
  (5, 5, 'comprehensive',               400, '2026-03-10', '2027-03-09', '[]'),
  (6, 6, 'comprehensive',               350, '2025-11-01', '2026-10-31', '["commercial use"]'),
  (7, 7, 'comprehensive',               250, '2024-01-01', '2024-12-31', '[]'),
  (8, 8, 'third party fire and theft',  300, '2025-12-01', '2026-11-30', '["glass damage","vandalism"]');

-- Prior claims. The current claim is not stored here.
INSERT INTO claim_history (history_id, customer_id, filing_date, claim_type) VALUES
  (1, 1, '2023-08-12', 'Collision'),
  (2, 2, '2026-01-20', 'Glass'),
  (3, 6, '2025-12-05', 'Collision'),
  (4, 6, '2026-02-14', 'Weather'),
  (5, 6, '2026-04-02', 'Vandalism'),
  (6, 3, '2025-10-01', 'Collision');

-- One claim per scenario, covering each routing outcome.
INSERT INTO claims (claim_id, customer_id, policy_id, filing_date, fnol_text, police_report_number) VALUES
  -- Low, covered, clean: Auto-Approve
  (1, 1, 1, '2026-03-03',
   'On 1 March 2026 I parked at Tesco on High Street and came back to find a small scrape on the rear bumper. Paint only, no dents. The car drives fine. Nobody was hurt and no other vehicle was involved.',
   NULL),
  -- Medium collision with third party, covered: Adjuster-Queue
  (2, 2, 2, '2026-04-10',
   'I was rear-ended at the lights on Mill Road on 8 April 2026 by a blue Ford Focus. My boot is crushed but I could drive home. The other driver gave me his details. I have a sore neck but did not need a doctor.',
   NULL),
  -- Theft with police report, covered: Adjuster-Queue (High severity)
  (3, 3, 3, '2026-02-18',
   'My car was stolen from outside my house in Leeds overnight on 16 February 2026. I found the space empty at 7am and called the police straight away.',
   'POL-2026-004512'),
  -- Not covered (theft excluded): Adjuster-Queue
  (4, 4, 4, '2026-01-12',
   'Someone broke into my car on 10 January 2026 in the Asda car park and took my laptop bag and the stereo.',
   'POL-2026-000377'),
  -- NEW_POLICY: filed 12 days after start: Investigation
  (5, 5, 5, '2026-03-22',
   'I hit a lamp post reversing out of a space in Bristol on 21 March 2026. The rear light is smashed and the bumper is dented. The car is still drivable. Nobody was hurt.',
   NULL),
  -- FREQUENT_CLAIMS: 3 prior within 12 months plus this one: Investigation
  (6, 6, 6, '2026-06-20',
   'A hailstorm on 18 June 2026 dented the bonnet and roof of my car while it was parked on the street in Manchester. No injuries.',
   NULL),
  -- THEFT_NO_POLICE_REPORT: Investigation
  (7, 3, 3, '2026-05-05',
   'My catalytic converter was stolen from my parked car in Leeds sometime last week. I did not report it to the police.',
   NULL),
  -- Missing required fields (no incident date, injuries unclear): Adjuster-Queue
  (8, 8, 8, '2026-07-01',
   'Someone hit my car and drove off. Front wing is damaged. Not sure when it happened, I noticed it when I came back to it.',
   NULL),
  -- Policy inactive on incident date: Adjuster-Queue
  (9, 7, 7, '2026-02-02',
   'A stone chipped my windscreen on the M6 on 30 January 2026. Small chip, no injuries.',
   NULL),
  -- Glass, covered, clean: Auto-Approve candidate
  (10, 1, 1, '2026-04-25',
   'A stone hit my windscreen on the A14 on 24 April 2026 and left a small crack in the corner. I can still see fine and drive. No injuries.',
   NULL);
