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
  LineChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
} from "cursor/canvas";

// Probabilities as PERCENT (9.5 = 9.5%)
const ACCESS_LADDER = [
  { label: "Tamil · no private $", pGovtPct: 4.3, pAccessPct: 4.3 },
  { label: "English · no private $", pGovtPct: 9.5, pAccessPct: 9.5 },
  { label: "English · can pay private", pGovtPct: 9.5, pAccessPct: 18.1 },
  { label: "English · $ · metro (knob)", pGovtPct: 11.6, pAccessPct: 21.9 },
];

const ZERO_SHARES_PCT = [
  { path: "Medicine", zeroPct: 44 },
  { path: "Engineering", zeroPct: 51 },
  { path: "No-seat mix", zeroPct: 52 },
  { path: "No college", zeroPct: 58 },
];

const HIST_BINS = ["₹0", "₹1–1L", "₹1–2.5L", "₹2.5–5L", "₹5–10L", "₹10–20L", "₹20L+"];
const HIST_ALL_MED = [0.44, 0.02, 0.12, 0.18, 0.16, 0.07, 0.01];
const HIST_ALL_ENG = [0.51, 0.02, 0.15, 0.18, 0.12, 0.03, 0.0];
const HIST_ALL_NOCOLLEGE = [0.58, 0.25, 0.14, 0.03, 0.0, 0.0, 0.0];

const KDE_X = ["0.4", "2.0", "3.6", "5.1", "6.7", "8.2", "9.8", "11.3", "12.9", "14.4"];
const KDE_MED = [0.08, 1.0, 0.95, 0.76, 0.56, 0.38, 0.25, 0.16, 0.11, 0.07];
const KDE_ENG = [0.08, 1.0, 0.69, 0.44, 0.26, 0.15, 0.09, 0.06, 0.03, 0.02];
const KDE_NONPROF = [0.48, 1.0, 0.25, 0.06, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0];
const KDE_NOCOLLEGE = [1.0, 0.11, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0];

// Profession-first wages (govt/private college share wage prior)
const WAGES = [
  { path: "Medicine", p50: 4.65, note: "govt & private college same prior" },
  { path: "Engineering", p50: 3.34, note: "World Bank anchor" },
  { path: "Law (knob)", p50: 2.63, note: "proxy" },
  { path: "Non-professional grad (knob)", p50: 1.58, note: "stylized" },
  { path: "No college (knob)", p50: 0.8, note: "stylized" },
];

// From attempt_repeater_sensitivity.csv — r = 71.42% among admitted
const ATTEMPT_SENS = [
  { rho: "0.5×", applicantsPct: 83.3, firstPct: 16.7 },
  { rho: "1.0×", applicantsPct: 71.4, firstPct: 28.6 },
  { rho: "1.5×", applicantsPct: 62.5, firstPct: 37.5 },
  { rho: "2.0×", applicantsPct: 55.5, firstPct: 44.5 },
  { rho: "3.0×", applicantsPct: 45.4, firstPct: 54.6 },
  { rho: "4.0×", applicantsPct: 38.5, firstPct: 61.5 },
];

export default function PrivilegeInequalityStory() {
  const theme = useHostTheme();

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 1160 }}>
      <Stack gap={8}>
        <Row gap={8} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Access by privilege · wages by profession</H1>
          <Pill tone="info">no fake demographics</Pill>
        </Row>
        <Text tone="secondary">
          Privilege changes who gets an affordable seat. Earnings curves are by career path.
          Caste / gender / parents’ income wage gaps need PLFS-class joints we do not have yet.
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="5.0×" label="Accessible-seat ladder" tone="danger" />
        <Stat value="~1.4×" label="Medicine / engineering median" tone="info" />
        <Stat value="71%" label="Admitted who were repeaters" />
        <Stat value="not ID’d" label="Mean attempts from that alone" tone="warning" />
      </Grid>

      <Divider />

      <H2>1. Annual earnings by profession (employed medians)</H2>
      <Callout tone="info" title="Govt vs private college is not a wage story here">
        Same physician wage prior for both college types. Private mainly buys access for
        families who can pay. Demographics are not invented as wage curves.
      </Callout>
      <BarChart
        categories={WAGES.map((r) => r.path)}
        series={[
          {
            name: "Median annual earnings if employed (₹ Lakh)",
            data: WAGES.map((r) => r.p50),
            tone: "info",
          },
        ]}
        height={280}
      />
      <Table
        headers={["Profession / path", "Median ₹L if employed", "Note"]}
        rows={WAGES.map((r) => [r.path, r.p50.toFixed(2), r.note])}
      />

      <H3>KDE among employed (₹ Lakh / year)</H3>
      <LineChart
        categories={KDE_X}
        series={[
          { name: "Medicine", data: KDE_MED, tone: "info" },
          { name: "Engineering", data: KDE_ENG, tone: "success" },
          { name: "Non-professional grad (knob)", data: KDE_NONPROF, tone: "warning" },
          { name: "No college (knob)", data: KDE_NOCOLLEGE, tone: "danger" },
        ]}
        height={280}
      />
      <H3>Histogram including zeros (display bins)</H3>
      <BarChart
        categories={HIST_BINS}
        series={[
          { name: "Medicine", data: HIST_ALL_MED, tone: "info" },
          { name: "Engineering", data: HIST_ALL_ENG, tone: "neutral" },
          { name: "No college (knob)", data: HIST_ALL_NOCOLLEGE, tone: "warning" },
        ]}
        height={240}
      />
      <Text tone="secondary" style={{ fontSize: 12, color: theme.text.secondary }}>
        Zeros ≈ employment / family-support filter for young adults, not street poverty.
        Source: make privilege · earnings_kde.csv
      </Text>

      <Divider />

      <H2>2. P(accessible / affordable seat), percent</H2>
      <BarChart
        categories={ACCESS_LADDER.map((r) => r.label)}
        series={[
          {
            name: "P(government offer), %",
            data: ACCESS_LADDER.map((r) => r.pGovtPct),
            tone: "info",
          },
          {
            name: "P(accessible seat), %",
            data: ACCESS_LADDER.map((r) => r.pAccessPct),
            tone: "danger",
          },
        ]}
        valueSuffix="%"
        height={260}
      />
      <Text tone="secondary" style={{ fontSize: 12, color: theme.text.secondary }}>
        Privilege axes (medium, affordability, metro knob) → access. Unaffordable private
        offers do not count.
      </Text>

      <Divider />

      <H2>3. From 71% admitted repeaters → applicant share (sensitivity)</H2>
      <Callout tone="warning" title="One observed share does not identify mean attempts">
        Observed r = P(repeater | admitted) = 71.4% (Rajan TN). Back out
        P(repeater | applicant) only under a labeled relative admit odds ρ. Full attempt
        counts (1, 2, 3, …) stay unidentified.
      </Callout>
      <BarChart
        categories={ATTEMPT_SENS.map((r) => r.rho)}
        series={[
          {
            name: "P(repeater | applicants), %",
            data: ATTEMPT_SENS.map((r) => r.applicantsPct),
            tone: "danger",
          },
          {
            name: "P(first attempt | applicants), %",
            data: ATTEMPT_SENS.map((r) => r.firstPct),
            tone: "info",
          },
        ]}
        valueSuffix="%"
        height={260}
      />
      <Table
        headers={[
          "ρ = P(admit|rep) / P(admit|first)",
          "Repeaters among applicants",
          "First-timers among applicants",
        ]}
        rows={ATTEMPT_SENS.map((r) => [
          r.rho,
          `${r.applicantsPct.toFixed(1)}%`,
          `${r.firstPct.toFixed(1)}%`,
        ])}
      />
      <Text tone="secondary" style={{ fontSize: 12, color: theme.text.secondary }}>
        ρ = 1 → applicants match admitted (71%). ρ &gt; 1 → fewer repeaters among applicants
        than among winners. Source: attempt_repeater_sensitivity.csv
      </Text>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Also real (admitted only)</CardHeader>
          <CardBody>
            <Text>~98.5% of admitted had coaching (2019–20) — winning pool, not causal return.</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Still not available</CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>Mean / distribution of attempt counts</Text>
              <Text>NEET coaching spend distribution</Text>
              <Text>Earnings by caste / gender / parents’ income / city</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H3>Share with ₹0 that year</H3>
      <BarChart
        categories={ZERO_SHARES_PCT.map((r) => r.path)}
        series={[
          {
            name: "Share with ₹0, %",
            data: ZERO_SHARES_PCT.map((r) => r.zeroPct),
            tone: "warning",
          },
        ]}
        valueSuffix="%"
        height={200}
      />

      <Text tone="secondary" style={{ color: theme.text.secondary }}>
        reports/PRIVILEGE_INEQUALITY_STORY.md · make privilege
      </Text>
    </Stack>
  );
}
