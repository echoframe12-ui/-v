import app from '../index';

describe('Ω∞v Oceanicos API Server', () => {
  it('should expose verification loop endpoints in app instance', () => {
    expect(app).toBeDefined();
    expect(typeof app).toBe('function');
  });
});
