#![allow(async_fn_in_trait)]

use std::fmt::{Display, Formatter};

#[derive(Debug)]
pub struct TransportError;

impl Display for TransportError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "transport failed")
    }
}

impl std::error::Error for TransportError {}

pub trait Transport {
    async fn send(&self, payload: &[u8]) -> Result<Vec<u8>, TransportError>;
}

pub struct Client<T: Transport> {
    transport: T,
}

impl<T: Transport> Client<T> {
    pub fn new(transport: T) -> Self {
        Self { transport }
    }

    pub async fn request(&self, input: &str) -> Result<String, TransportError> {
        let bytes = self.transport.send(input.as_bytes()).await?;
        String::from_utf8(bytes).map_err(|_| TransportError)
    }
}

pub struct SessionGuard {
    closed: bool,
}

impl SessionGuard {
    pub fn close(mut self) {
        self.closed = true;
    }
}

impl Drop for SessionGuard {
    fn drop(&mut self) {
        if !self.closed {
            eprintln!("closing fixture session");
        }
    }
}
