import { describe, expect, it } from "vitest";
import { baselineMedian, engagementRate, isOutlier, median, outlierMultiplier, refreshBucket } from "./scoring";

describe("median", () => {
  it("handles odd, even, empty", () => {
    expect(median([3, 1, 2])).toBe(2);
    expect(median([4, 1, 3, 2])).toBe(2.5);
    expect(median([])).toBeNull();
  });
});

describe("baselineMedian", () => {
  it("uses only the 20 most recent videos", () => {
    const old = Array.from({ length: 30 }, (_, i) => ({ views: 1_000_000, publishedAt: new Date(2020, 0, i + 1) }));
    const recent = Array.from({ length: 20 }, (_, i) => ({ views: 1000 + i, publishedAt: new Date(2026, 0, i + 1) }));
    expect(baselineMedian([...old, ...recent])).toBe(1009.5);
  });
});

describe("outlier scoring", () => {
  it("normalizes against the creator baseline, not raw views", () => {
    // 100k views on a 2M-follower account with 400k median = underperformer
    expect(outlierMultiplier(100_000, 400_000)).toBe(0.25);
    // 100k views on a small account with 3k median = explosive outlier
    const om = outlierMultiplier(100_000, 3_000);
    expect(om).toBe(33.33);
    expect(isOutlier(om)).toBe(true);
    expect(isOutlier(2.49)).toBe(false);
    expect(isOutlier(2.5)).toBe(true);
    expect(outlierMultiplier(10, 0)).toBeNull();
  });

  it("weights engagement actions", () => {
    expect(engagementRate({ views: 1000, likes: 50, comments: 10, saves: 5, shares: 5 })).toBe(10.5);
    expect(engagementRate({ views: 0, likes: 1, comments: 0, saves: 0, shares: 0 })).toBeNull();
  });
});

describe("refreshBucket", () => {
  const now = new Date("2026-09-20T12:00:00Z");
  it("maps age to d1/d3/d7", () => {
    expect(refreshBucket(new Date("2026-09-19T06:00:00Z"), now)).toBe("d1");
    expect(refreshBucket(new Date("2026-09-17T06:00:00Z"), now)).toBe("d3");
    expect(refreshBucket(new Date("2026-09-13T06:00:00Z"), now)).toBe("d7");
    expect(refreshBucket(new Date("2026-09-15T06:00:00Z"), now)).toBeNull();
  });
});
