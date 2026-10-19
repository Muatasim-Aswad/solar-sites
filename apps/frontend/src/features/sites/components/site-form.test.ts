import { expect, test } from "vite-plus/test";
import { siteSchema } from "./site-form";

const validSite = {
  clientName: "Sample household",
  address: "Example street 10",
  latitude: 52.08,
  longitude: 4.31,
  roofAreaM2: 40,
  peakKwp: 5,
};

test("accepts a valid site and trims the client name and address", () => {
  expect(
    siteSchema.parse({
      ...validSite,
      clientName: "  Sample household  ",
      address: "  Example street 10  ",
    }),
  ).toEqual(validSite);
});

test.each(["clientName", "address"] as const)("requires a nonblank %s", (field) => {
  const result = siteSchema.safeParse({ ...validSite, [field]: "   " });

  expect(result.success).toBe(false);
  if (!result.success) {
    expect(result.error.issues[0]?.path).toEqual([field]);
  }
});

test.each(["latitude", "longitude", "peakKwp"] as const)(
  "requires a number when the %s input is empty",
  (field) => {
    const result = siteSchema.safeParse({ ...validSite, [field]: Number.NaN });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.path).toEqual([field]);
    }
  },
);

test.each([
  { latitude: -90, longitude: -180 },
  { latitude: 90, longitude: 180 },
])("accepts coordinate boundaries $latitude, $longitude", (coordinates) => {
  expect(siteSchema.safeParse({ ...validSite, ...coordinates }).success).toBe(true);
});

test.each([
  ["latitude", -91],
  ["latitude", 91],
  ["longitude", -181],
  ["longitude", 181],
] as const)("rejects %s outside its coordinate range: %s", (field, value) => {
  const result = siteSchema.safeParse({ ...validSite, [field]: value });

  expect(result.success).toBe(false);
  if (!result.success) {
    expect(result.error.issues[0]?.path).toEqual([field]);
  }
});

test.each([
  ["peakKwp", 0],
  ["peakKwp", -1],
  ["peakKwp", 100_001],
  ["roofAreaM2", 0],
  ["roofAreaM2", -1],
  ["roofAreaM2", 1_000_001],
] as const)("rejects %s outside its positive size range: %s", (field, value) => {
  const result = siteSchema.safeParse({ ...validSite, [field]: value });

  expect(result.success).toBe(false);
  if (!result.success) {
    expect(result.error.issues[0]?.path).toEqual([field]);
  }
});

test("allows the optional roof area to be left empty", () => {
  expect(siteSchema.parse({ ...validSite, roofAreaM2: null }).roofAreaM2).toBeNull();
});
