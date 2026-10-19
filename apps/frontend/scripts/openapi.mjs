import { readFile, writeFile } from "node:fs/promises";
import openapiTS, { astToString } from "openapi-typescript";

const source = new URL("../../backend/openapi.json", import.meta.url);
const destination = new URL("../src/infra/api/schema.d.ts", import.meta.url);
const output = astToString(await openapiTS(source));
if (process.argv.includes("--check")) {
  if ((await readFile(destination, "utf8")) !== output) {
    console.error("API types differ from backend OpenAPI. Run pnpm run api:generate.");
    process.exitCode = 1;
  } else {
    console.log("Generated API types match backend OpenAPI.");
  }
} else {
  await writeFile(destination, output);
  console.log("Generated src/infra/api/schema.d.ts from backend OpenAPI.");
}
