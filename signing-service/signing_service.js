const express = require('express');
const TonWeb = require('tonweb');
const TonWebMnemonic = require('tonweb-mnemonic');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
app.use(express.json());

// Configuration from environment variables
const API_SECRET_KEY = process.env.API_SECRET_KEY;
const SENDER_MNEMONIC = process.env.SENDER_WALLET_SEED.split(' ');
const JETTON_MASTER = process.env.CHAMBY_JETTON_CONTRACT;
const MAX_AMOUNT_PER_TX = parseInt(process.env.MAX_AMOUNT_PER_TX || '100000');
const TONCENTER_API_KEY = process.env.TONCENTER_API_KEY || '';

// Initialize TonWeb
const tonweb = new TonWeb(new TonWeb.HttpProvider('https://toncenter.com/api/v2/jsonRPC', {
    apiKey: TONCENTER_API_KEY
}));

// Rate limiting
const requestHistory = {};
const RATE_LIMIT_PER_MINUTE = parseInt(process.env.RATE_LIMIT_PER_MINUTE || '10');

function checkRateLimit(ip) {
    const now = Date.now();
    const minuteAgo = now - 60000;

    if (!requestHistory[ip]) {
        requestHistory[ip] = [];
    }

    requestHistory[ip] = requestHistory[ip].filter(time => time > minuteAgo);

    if (requestHistory[ip].length >= RATE_LIMIT_PER_MINUTE) {
        return false;
    }

    requestHistory[ip].push(now);
    return true;
}

// Middleware for API key verification
function requireApiKey(req, res, next) {
    const key = req.headers['x-api-key'];
    if (!key) {
        return res.status(401).json({error: 'API key required'});
    }
    if (key !== API_SECRET_KEY) {
        return res.status(403).json({error: 'Invalid API key'});
    }
    next();
}

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'ton-signing-service',
        mode: 'PRODUCTION-TONWEB',
        timestamp: new Date().toISOString()
    });
});

// Send tokens
app.post('/api/v1/send_tokens', requireApiKey, async (req, res) => {
    try {
        const clientIp = req.ip;

        if (!checkRateLimit(clientIp)) {
            console.log(`❌ Rate limit exceeded for ${clientIp}`);
            return res.status(429).json({
                success: false,
                error: 'Rate limit exceeded'
            });
        }

        const {recipient, amount} = req.body;

        if (!recipient || !amount) {
            return res.status(400).json({
                success: false,
                error: 'Missing parameters: recipient and amount required'
            });
        }

        if (amount > MAX_AMOUNT_PER_TX) {
            return res.status(400).json({
                success: false,
                error: `Amount exceeds maximum (${MAX_AMOUNT_PER_TX})`
            });
        }

        console.log(`🚀 Sending ${amount} tokens to ${recipient}`);

        const keyPair = await TonWebMnemonic.mnemonicToKeyPair(SENDER_MNEMONIC);

        const WalletClass = tonweb.wallet.all['v4R2'];
        const wallet = new WalletClass(tonweb.provider, {
            publicKey: keyPair.publicKey
        });

        const walletAddress = await wallet.getAddress();
        console.log(`✅ Wallet: ${walletAddress.toString(true, true, true)}`);

        // Get seqno
        const seqno = await wallet.methods.seqno().call() || 0;
        console.log(`✅ Seqno: ${seqno}`);

        // Get sender's Jetton Wallet address
        const jettonMinter = new TonWeb.token.jetton.JettonMinter(tonweb.provider, {
            address: JETTON_MASTER
        });

        const senderJettonWalletAddress = await jettonMinter.getJettonWalletAddress(walletAddress);
        console.log(`✅ Sender Jetton Wallet: ${senderJettonWalletAddress.toString(true, true, true)}`);

        // Create Jetton Wallet object
        const jettonWallet = new TonWeb.token.jetton.JettonWallet(tonweb.provider, {
            address: senderJettonWalletAddress
        });

        // Convert amount (9 decimals)
        const jettonAmount = new TonWeb.utils.BN(amount).mul(new TonWeb.utils.BN(1e9));

        console.log(`💰 Jetton amount: ${jettonAmount.toString()}`);

        // Create Jetton transfer body
        const transferBody = await jettonWallet.createTransferBody({
            jettonAmount: jettonAmount,
            toAddress: new TonWeb.utils.Address(recipient),
            forwardAmount: TonWeb.utils.toNano('0.01'),
            forwardPayload: new Uint8Array(),
            responseAddress: walletAddress
        });

        // Create and send transaction
        const transfer = wallet.methods.transfer({
            secretKey: keyPair.secretKey,
            toAddress: senderJettonWalletAddress.toString(true, true, true),
            amount: TonWeb.utils.toNano('0.05'),
            seqno: seqno,
            payload: transferBody,
            sendMode: 3
        });

        console.log(`📤 Sending transaction...`);

        const result = await transfer.send();

        console.log(`✅ Transaction sent!`);

        res.json({
            success: true,
            tx_hash: result.toString(),
            note: 'Real Jetton transfer via tonweb',
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        console.error(error.stack);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get balance
app.get('/api/v1/balance', requireApiKey, async (req, res) => {
    try {
        const keyPair = await TonWebMnemonic.mnemonicToKeyPair(SENDER_MNEMONIC);

        const WalletClass = tonweb.wallet.all['v4R2'];
        const wallet = new WalletClass(tonweb.provider, {
            publicKey: keyPair.publicKey
        });

        const walletAddress = await wallet.getAddress();
        const balance = await tonweb.provider.getBalance(walletAddress.toString(true, true, true));

        res.json({
            success: true,
            balance: parseFloat(TonWeb.utils.fromNano(balance)),
            address: walletAddress.toString(true, true, true)
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
    console.log('============================================================');
    console.log('🚀 TON SIGNING SERVICE - PRODUCTION');
    console.log('============================================================');
    console.log(`✅ Mode: Node.js + tonweb`);
    console.log(`✅ Server running on port ${PORT}`);
    console.log(`✅ REAL Jetton transfers enabled!`);
    console.log('============================================================');
});
