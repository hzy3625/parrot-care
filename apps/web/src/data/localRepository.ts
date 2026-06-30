import { categoryById } from '../domain/catalog'
import type { AnomalyEvent, AudioAsset, DashboardSummary, EventStatus, NewLocalEvent, Note } from '../types'

const DATABASE_NAME = 'parrot-care-local'
const DATABASE_VERSION = 1
const EVENT_STORE = 'events'
const AUDIO_STORE = 'audio'

const sampleEvents: AnomalyEvent[] = [
  {
    id: 'sample-night-fright',
    categoryId: 'night_fright',
    type: '夜间惊飞',
    timestamp: new Date(Date.now() - 42 * 60 * 1000).toISOString(),
    severity: 'high',
    confidence: 0.92,
    status: 'reviewing',
    duration: 12,
    source: 'sample',
    notes: [
      {
        id: 'sample-note-1',
        content: '凌晨出现连续扑翅声，建议检查夜灯和笼具周边环境。',
        timestamp: new Date(Date.now() - 35 * 60 * 1000).toISOString(),
        author: '本地助手',
      },
    ],
  },
  {
    id: 'sample-scream',
    categoryId: 'scream',
    type: '持续尖叫',
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    severity: 'medium',
    confidence: 0.84,
    status: 'pending',
    duration: 9,
    source: 'sample',
    notes: [],
  },
  {
    id: 'sample-normal',
    categoryId: 'normal_chirp',
    type: '正常鸣叫',
    timestamp: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
    severity: 'low',
    confidence: 0.96,
    status: 'resolved',
    duration: 8,
    source: 'sample',
    notes: [],
  },
]

const requestAsPromise = <T>(request: IDBRequest<T>) =>
  new Promise<T>((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('本地数据库操作失败'))
  })

const transactionDone = (transaction: IDBTransaction) =>
  new Promise<void>((resolve, reject) => {
    transaction.oncomplete = () => resolve()
    transaction.onerror = () => reject(transaction.error ?? new Error('本地数据库事务失败'))
    transaction.onabort = () => reject(transaction.error ?? new Error('本地数据库事务已取消'))
  })

let databasePromise: Promise<IDBDatabase> | null = null

const openDatabase = () => {
  if (databasePromise) return databasePromise

  databasePromise = new Promise<IDBDatabase>((resolve, reject) => {
    if (!('indexedDB' in window)) {
      reject(new Error('当前浏览器不支持本地数据存储'))
      return
    }

    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION)
    request.onupgradeneeded = () => {
      const database = request.result
      if (!database.objectStoreNames.contains(EVENT_STORE)) {
        const events = database.createObjectStore(EVENT_STORE, { keyPath: 'id' })
        events.createIndex('timestamp', 'timestamp')
      }
      if (!database.objectStoreNames.contains(AUDIO_STORE)) {
        database.createObjectStore(AUDIO_STORE, { keyPath: 'id' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('无法打开本地数据库'))
  })

  return databasePromise
}

const createId = (prefix: string) =>
  `${prefix}-${globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`}`

const seedIfEmpty = async () => {
  const database = await openDatabase()
  const countTransaction = database.transaction(EVENT_STORE, 'readonly')
  const count = await requestAsPromise(countTransaction.objectStore(EVENT_STORE).count())
  await transactionDone(countTransaction)
  if (count > 0) return

  const seedTransaction = database.transaction(EVENT_STORE, 'readwrite')
  const store = seedTransaction.objectStore(EVENT_STORE)
  sampleEvents.forEach((event) => store.put(event))
  await transactionDone(seedTransaction)
}

export const localRepository = {
  async listEvents(): Promise<AnomalyEvent[]> {
    await seedIfEmpty()
    const database = await openDatabase()
    const transaction = database.transaction(EVENT_STORE, 'readonly')
    const events = await requestAsPromise(transaction.objectStore(EVENT_STORE).getAll() as IDBRequest<AnomalyEvent[]>)
    await transactionDone(transaction)
    return events.sort((first, second) => second.timestamp.localeCompare(first.timestamp))
  },

  async getEvent(id: string): Promise<AnomalyEvent | undefined> {
    await seedIfEmpty()
    const database = await openDatabase()
    const transaction = database.transaction(EVENT_STORE, 'readonly')
    const event = await requestAsPromise(transaction.objectStore(EVENT_STORE).get(id) as IDBRequest<AnomalyEvent | undefined>)
    await transactionDone(transaction)
    return event
  },

  async createEvent(input: NewLocalEvent): Promise<AnomalyEvent> {
    const database = await openDatabase()
    const category = categoryById(input.categoryId)
    const eventId = createId('event')
    const audioId = createId('audio')
    const timestamp = new Date().toISOString()
    const event: AnomalyEvent = {
      id: eventId,
      categoryId: category.id,
      type: category.name,
      timestamp,
      severity: category.severity,
      confidence: null,
      status: 'pending',
      duration: input.duration,
      source: input.source,
      audioId,
      notes: [],
    }
    const asset: AudioAsset = {
      id: audioId,
      blob: input.audio,
      mimeType: input.audio.type || 'audio/webm',
      createdAt: timestamp,
    }

    const transaction = database.transaction([EVENT_STORE, AUDIO_STORE], 'readwrite')
    transaction.objectStore(EVENT_STORE).put(event)
    transaction.objectStore(AUDIO_STORE).put(asset)
    await transactionDone(transaction)
    return event
  },

  async getAudio(audioId: string): Promise<Blob | undefined> {
    const database = await openDatabase()
    const transaction = database.transaction(AUDIO_STORE, 'readonly')
    const asset = await requestAsPromise(transaction.objectStore(AUDIO_STORE).get(audioId) as IDBRequest<AudioAsset | undefined>)
    await transactionDone(transaction)
    return asset?.blob
  },

  async updateStatus(id: string, status: EventStatus): Promise<AnomalyEvent> {
    const event = await this.getEvent(id)
    if (!event) throw new Error('记录不存在')
    const updated = { ...event, status }
    const database = await openDatabase()
    const transaction = database.transaction(EVENT_STORE, 'readwrite')
    transaction.objectStore(EVENT_STORE).put(updated)
    await transactionDone(transaction)
    return updated
  },

  async updateCategory(id: string, categoryId: string): Promise<AnomalyEvent> {
    const event = await this.getEvent(id)
    if (!event) throw new Error('记录不存在')
    const category = categoryById(categoryId)
    const updated = {
      ...event,
      categoryId: category.id,
      type: category.name,
      severity: category.severity,
    }
    const database = await openDatabase()
    const transaction = database.transaction(EVENT_STORE, 'readwrite')
    transaction.objectStore(EVENT_STORE).put(updated)
    await transactionDone(transaction)
    return updated
  },

  async addNote(id: string, content: string): Promise<AnomalyEvent> {
    const event = await this.getEvent(id)
    if (!event) throw new Error('记录不存在')
    const note: Note = {
      id: createId('note'),
      content: content.trim(),
      timestamp: new Date().toISOString(),
      author: '我',
    }
    const updated = { ...event, notes: [...event.notes, note] }
    const database = await openDatabase()
    const transaction = database.transaction(EVENT_STORE, 'readwrite')
    transaction.objectStore(EVENT_STORE).put(updated)
    await transactionDone(transaction)
    return updated
  },

  async summary(): Promise<DashboardSummary> {
    const events = await this.listEvents()
    const today = new Date().toDateString()
    return {
      total: events.length,
      pending: events.filter((event) => event.status === 'pending' || event.status === 'reviewing').length,
      highRisk: events.filter((event) => event.severity === 'high' || event.severity === 'critical').length,
      today: events.filter((event) => new Date(event.timestamp).toDateString() === today).length,
    }
  },
}
