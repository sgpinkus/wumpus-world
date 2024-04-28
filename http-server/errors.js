/**
 * Use this Error subexport class to indicate an Error condition that is consistent with a specific HTTP status code and when
 * you would like to indicate that to the client of a given UseVerb library. In fact, we just have all our custom errors
 * extending this and provided some HTTP error status code, even though it's sometimes vague or possibly innaccurate.
 * @see https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
 * @param {string} message
 * @param {number} status http equivalent status code.
 * @param {Error} previous the previous error that caused this Error if any.
 */
export class HttpEquivalentError extends Error {
  constructor(message, status = 500, previous) {
    let data;
    if (typeof message !== 'string' && message !== undefined) {
      data = message.data;
      message = message.message;
    }
    super(message);
    if (data !== undefined) this.data = data;
    this.name = 'HttpEquivalentError';
    this.status = status;
    this.previous = previous;
  }
}

/**
 * Client request could not be processed because some logical pre-requisite condition(s) failed to be met due to
 * improper request or usage by *client*.
 * @extends HttpEquivalentError
 */
export class LogicError extends HttpEquivalentError {
  constructor(message, status = 422, previous) {
    super(message, status, previous);
    this.name = 'LogicError';
  }
}


/**
 * Used by Models to indicate required resource not found by some model or static method. Some methods may return a
 * falsely value instead.
 * @param {boolean} override If true `name` param is whole message.
 * @extends HttpEquivalentError
 */
export class NotFoundError extends HttpEquivalentError {
  constructor(name, status = 404, previous, override = false) {
    super(override ? name : `${name.replace(/^\b\w/, c => c.toUpperCase())} not found.`, status, previous);
    this.name = 'NotFoundError';
  }
}


/**
 * Only used if the user is not authenticated or there is something wrong with their credentials. Use PermissionError
 * if the user is authenticated but not allowed to do the thing.
 * @extends HttpEquivalentError
 */
export class AuthenticationError extends HttpEquivalentError {
  constructor(message = 'Authentication required.', status = 401, previous) {
    super(message, status, previous);
    this.name = 'AuthenticationError';
  }
}


/**
 * The user is authenticated but not allowed to do a thing.
 * @extends HttpEquivalentError
 */
export class PermissionError extends HttpEquivalentError {
  constructor(message = 'Permission denied.', status = 403, previous) {
    super(message, status, previous);
    this.name = 'PermissionError';
  }
}

/**
 * Indicate a beyond limits error.
 * @extends HttpEquivalentError
 */
export class LimitsError extends HttpEquivalentError {
  constructor(message, status = 422, previous) {
    super(message, status, previous);
    this.name = 'LimitsError';
  }
}

/**
 * @extends HttpEquivalentError
 */
export class UnsupportedMimeTypeError extends HttpEquivalentError {
  constructor(message, status = 415, previous) {
    super(message, status, previous);
    this.name = 'UnsupportedMimeTypeError';
  }
}

/**
 * @extends HttpEquivalentError
 */
export class ValidationError extends HttpEquivalentError {
  constructor(message, status = 400, previous) {
    super(message, status, previous);
    this.name = 'ValidationError';
  }
}

/**
 * @extends HttpEquivalentError
 */
export class DuplicateError extends HttpEquivalentError {
  constructor(message, status = 422, previous) {
    super(message, status, previous);
    this.name = 'DuplicateError';
  }
}

/**
 * @extends HttpEquivalentError
 */
export class PaymentRequiredError extends HttpEquivalentError {
  constructor(message, status = 402, previous) {
    super(message, status, previous);
    this.name = 'PaymentRequiredError';
  }
}

/**
 * Client did not provide required input.
 * @extends HttpEquivalentError
 */
export class MissingInputError extends HttpEquivalentError {
  constructor(name, status = 422, previous) {
    super('Missing required argument' + (name ? ` '${name}'.` : '.'), status, previous);
    this.name = 'MissingInputError';
  }
}

/**
 * Client provided input/argument that is not within valid bounds/range required by throwing method. AKA InvalidInputError.
 * Use this to indicate the system's external client is in error by providing an invalid argument.
 * @extends HttpEquivalentError
 */
export class InvalidInputError extends HttpEquivalentError {
  constructor(message, status = 422, previous) {
    super(message, status, previous);
    this.name = 'InvalidInputError';
  }
}

/**
 * Missed required argument to a function call somewhere internal. This error should really be done by static analysis
 * and typing .. never the less currently sometimes it's better run time check this rather than allowing some more mysterious
 * error to be thrown because of a missing argument. Border line not useful over just throwing an error.
 * @extends HttpEquivalentError
 */
export class MissingArgumentError extends HttpEquivalentError {
  constructor(name, status = 500, previous) {
    super('Missing required argument' + (name ? ` '${name}'.` : '.'), status, previous);
    this.name = 'MissingArgumentError';
  }
}

/**
 * @see MissingArgumentError
 * @extends HttpEquivalentError
 */
export class InvalidArgumentError extends HttpEquivalentError {
  constructor(message, status = 500, previous) {
    super(message, status, previous);
    this.name = 'InvalidArgumentError';
  }
}
