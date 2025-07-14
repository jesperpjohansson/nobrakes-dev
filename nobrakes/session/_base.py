"""
Abstract base interfaces for request/response/session handling.

These adapters standardize the interface for asynchronous HTTP sessions and responses,
allowing integration with the `nobrakes` framework.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, MutableMapping
from contextlib import AbstractAsyncContextManager


class ResponseAdapter[ResponseT](ABC):
    """
    Abstract base class for HTTP response adapters.

    Parameters
    ----------
    adaptee : ResponseT
        The adaptee.

    """

    def __init__(self, adaptee: ResponseT) -> None:
        self.adaptee = adaptee

    @abstractmethod
    async def read(self) -> bytes:
        """
        Asynchronously read the full response body as bytes.

        Returns
        -------
        bytes
            The complete response payload.

        """

    @abstractmethod
    def iter_chunks(self, n: int | None = None) -> AsyncIterator[bytes]:
        """
        Iterate over the response body in chunks.

        Parameters
        ----------
        n : int, optional
            Number of bytes per chunk. If None, the implementation may
            choose a reasonable default chunk size.

        Returns
        -------
        AsyncIterator[bytes]
            Asynchronous iterator yielding bytes chunks.
        """

    @abstractmethod
    def iter_lines(self) -> AsyncIterator[bytes]:
        """
        Iterate over the response body line by line.

        Returns
        -------
        AsyncIterator[bytes]
            Asynchronous iterator over lines.

        """

    @abstractmethod
    def raise_for_status(self) -> object:
        """Raise an exception if the HTTP response indicates an error."""


class SessionAdapter[ClientT, ResponseT](ABC):
    """
    Abstract base class for asynchronous HTTP client session adapters.

    Parameters
    ----------
    adaptee : ClientT
        The adaptee.

    """

    def __init__(self, adaptee: ClientT) -> None:
        self.adaptee = adaptee

    @property
    @abstractmethod
    def headers(self) -> MutableMapping[str, str]:
        """
        Expose the session's mutable headers.

        Returns
        -------
        MutableMapping
            Mapping of header names to values.

        """

    @abstractmethod
    def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """
        Perform an HTTP request using the specified method and URL.

        Parameters
        ----------
        method : str
            HTTP method, e.g., "get", "post".
        url : str
            Target URL.
        **kwargs : Any
            Additional keyword arguments supported by the underlying session.

        Returns
        -------
        AbstractAsyncContextManager[ResponseAdapter[ResponseT]]
            An asynchoronous context manager yielding an adapted response.

        """

    def get(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP GET request."""
        return self.request("get", url, **kwargs)

    def post(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP POST request."""
        return self.request("post", url, **kwargs)

    def put(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP PUT request."""
        return self.request("put", url, **kwargs)

    def delete(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP DELETE request."""
        return self.request("delete", url, **kwargs)

    def head(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP HEAD request."""
        return self.request("head", url, **kwargs)

    def options(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP OPTIONS request."""
        return self.request("options", url, **kwargs)

    def patch(
        self,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[ResponseAdapter[ResponseT]]:
        """Perform an HTTP PATCH request."""
        return self.request("patch", url, **kwargs)
