import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: 15,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 20,
    },
  },
};

export default function () {
  http.post(
    'http://localhost:8000/webhooks/payment-status',
    JSON.stringify({
      payment_id: '123',
      status: 'completed'
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'X-Signature': 'test-signature'
      }
    }
  );

  sleep(1);
}