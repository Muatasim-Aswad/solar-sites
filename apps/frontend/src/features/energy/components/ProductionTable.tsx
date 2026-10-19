import type { components } from "../../../infra/api/schema";
import { number } from "../../../shared/numbers";
import { Table } from "../../../shared/ui/table";

const months = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export function ProductionTable({
  production,
}: {
  production: components["schemas"]["ProductionOutput"];
}) {
  return (
    <Table variant="production">
      <caption className="sr-only">Estimated monthly solar production in kilowatt-hours</caption>
      <thead>
        <tr>
          <th scope="col">Month</th>
          <th scope="col">Production (kWh)</th>
        </tr>
      </thead>
      <tbody>
        {production.monthlyKwh.map(({ month, kwh }) => (
          <tr key={month}>
            <th scope="row">{months[month - 1]}</th>
            <td>{number(kwh)}</td>
          </tr>
        ))}
      </tbody>
      <tfoot className="border-t-2 border-line-strong font-bold">
        <tr>
          <th scope="row">Yearly total</th>
          <td>{number(production.yearlyKwh)}</td>
        </tr>
      </tfoot>
    </Table>
  );
}
