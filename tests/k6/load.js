import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';

const unexpectedFailures = new Counter('unexpected_failures');
const apiKey = __ENV.API_KEY || 'hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4';
const targetVus = Number(__ENV.VUS || 1);
const baseUrl = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  scenarios: {
    listChecks: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: targetVus },
        { duration: '60s', target: targetVus },
        { duration: '5s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.get(`${baseUrl}/api/v3/checks/`, {
    headers: { 'X-Api-Key': apiKey },
    tags: { name: 'listChecks' },
  });
  if (!check(response, { 'status is 200': (r) => r.status === 200 })) {
    unexpectedFailures.add(1);
  }
  sleep(0.3);
}
