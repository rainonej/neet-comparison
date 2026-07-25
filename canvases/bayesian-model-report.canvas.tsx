import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
} from "cursor/canvas";

const COMPARISON = [
  {
    profile: "neutral",
    qualify: 0.564,
    capacity: 0.0555,
    tnRatio: 2.35,
    coachingSd: 0.0,
    medEarn: 310284,
    engEarn: 214271,
    zeroMed: 0.452,
  },
  {
    profile: "conservative",
    qualify: 0.564,
    capacity: 0.0555,
    tnRatio: 2.35,
    coachingSd: 0.08,
    medEarn: 311487,
    engEarn: 215225,
    zeroMed: 0.446,
  },
  {
    profile: "reasonable",
    qualify: 0.564,
    capacity: 0.0555,
    tnRatio: 2.35,
    coachingSd: 0.14,
    medEarn: 309134,
    engEarn: 214311,
    zeroMed: 0.447,
  },
];

const PPC_QUALIFY = [
  { label: "SECL 23-24", observed: 0.975, residual: 0.411, selection: "very strong" },
  { label: "SECL 24-25", observed: 0.775, residual: 0.211, selection: "very strong" },
  { label: "APSWREIS 24-25", observed: 0.794, residual: 0.230, selection: "very strong" },
  { label: "Sigaram 2018", observed: 0.167, residual: -0.397, selection: "low" },
  { label: "Sigaram 2019", observed: 0.163, residual: -0.401, selection: "low" },
  { label: "Sigaram 2020", observed: 0.474, residual: -0.09, selection: "low" },
];

export default function BayesianModelReport() {
  const theme = useHostTheme();
  const cons = COMPARISON[1];

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 1100 }}>
      <Stack gap={8}>
        <Row gap={8} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Bayesian evidence model</H1>
          <Pill tone="info">v0.3.0</Pill>
          <Pill tone="neutral">default: conservative</Pill>
        </Row>
        <Text tone="secondary">
          Conjugate updates on in-repo public evidence only. No gated PLFS/HCES/NFHS
          microdata. Coaching cohorts are PPC targets, not treatment-effect updates.
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="56.4%" label="NEET qualify rate (ESS ~2.33M)" />
        <Stat value="18.0" label="Appeared per MBBS seat" />
        <Stat value="2.35×" label="TN Eng/Tamil govt rate ratio" />
        <Stat value="₹96k" label="Medicine − eng. mean earnings" tone="info" />
      </Grid>

      <Callout tone="warning" title="What this is not">
        Not a causal effect of coaching or of barely clearing a cutoff. Not P(seat |
        score, income, caste, domicile, attempt). Employment rates are broad graduate
        proxies until PLFS is available.
      </Callout>

      <Divider />

      <H2>Scarcity and state inequality</H2>
      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>National 2024 ecology</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Qualification is pinned by reconciled NTA counts (1,315,853 /
                2,333,162). Capacity uses the NMC seat snapshot with small ESS because
                the page is dynamic — point rate 5.55%, wide CI.
              </Text>
              <Table
                headers={["Quantity", "Mean", "Notes"]}
                rows={[
                  ["Qualify rate", "0.5640", "Full-count Beta update"],
                  ["Seats / appeared", "0.0555", "Snapshot ESS ≈ 34"],
                  ["Qualified / seat", "10.2", "Derived"],
                  ["AIQ MBBS share", "84.8%", "MCC allotment mix"],
                ]}
              />
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Tamil Nadu medium (holdout 2020–21)</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                English-medium government allotment posterior 8.77% vs Tamil 3.73%.
                Holdout year was more favorable overall (abs. errors ~0.036 / 0.041)
                but the English advantage direction holds.
              </Text>
              <H3>TN post-NEET govt allotment rates</H3>
              <BarChart
                categories={["English medium", "Tamil medium"]}
                series={[
                  {
                    name: "Posterior mean rate",
                    data: [0.0877, 0.0373],
                  },
                ]}
                height={200}
              />
              <Text tone="secondary" style={{ fontSize: 12, color: theme.text.secondary }}>
                Source: Justice A.K. Rajan Committee Table 7.18 · calibrated on
                post-NEET years except 2020–21
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>Prior-profile sensitivity</H2>
      <Text tone="secondary">
        Complete counts dominate. Profiles mainly change the coaching score-shift
        prior and weakly identified employment widths.
      </Text>
      <Table
        headers={[
          "Profile",
          "Qualify",
          "TN ratio",
          "Coaching prior (SD)",
          "Med. mean ₹",
          "Med. zero share",
        ]}
        rows={COMPARISON.map((row) => [
          row.profile,
          row.qualify.toFixed(3),
          row.tnRatio.toFixed(2),
          row.coachingSd.toFixed(2),
          Math.round(row.medEarn).toLocaleString("en-IN"),
          row.zeroMed.toFixed(2),
        ])}
      />
      <H3>One-year mean earnings by path (conservative)</H3>
      <BarChart
        categories={["Medicine", "Engineering", "Other graduate"]}
        series={[
          {
            name: "Mean annual earnings (INR)",
            data: [cons.medEarn, cons.engEarn, 107231],
          },
        ]}
        valuePrefix="₹"
        height={220}
      />
      <Text tone="secondary" style={{ fontSize: 12, color: theme.text.secondary }}>
        Source: career gates × World Bank wage anchors · Monte Carlo 40k draws · zeros
        retained for non-completion / non-employment
      </Text>

      <Divider />

      <H2>Coaching PPC (no effect update)</H2>
      <Text>
        Observed cohort qualify rates versus national posterior mean 0.564. Residuals
        diagnose selection intensity, not a coaching LATE.
      </Text>
      <H3>Qualify rate: observed minus national posterior</H3>
      <BarChart
        categories={PPC_QUALIFY.map((row) => row.label)}
        series={[
          {
            name: "Observed − predicted",
            data: PPC_QUALIFY.map((row) => row.residual),
          },
        ]}
        beginAtZero={false}
        height={240}
      />
      <Table
        headers={["Cohort", "Observed qualify", "Residual", "Selection"]}
        rows={PPC_QUALIFY.map((row) => [
          row.label,
          row.observed.toFixed(3),
          (row.residual > 0 ? "+" : "") + row.residual.toFixed(3),
          row.selection,
        ])}
      />
      <Callout tone="info" title="Validation reading">
        No single coaching shift can jointly fit elite selected residential programs
        (+0.2 to +0.4 vs national) and open-access Sigaram cohorts (−0.4). That failure
        mode is intentional.
      </Callout>

      <Divider />

      <H3>Artifacts</H3>
      <Text tone="secondary" style={{ color: theme.text.secondary }}>
        reports/BAYESIAN_MODEL_REPORT.md · data/processed/bayesian/*.csv · make bayes
      </Text>
    </Stack>
  );
}
